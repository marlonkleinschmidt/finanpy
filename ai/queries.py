"""Pure read-only ORM queries that take user_id as first parameter.

Every public function runs a fixed number of queries and returns JSON ready
data: money and percentages as text, dates as ISO text. Invalid arguments
raise ValueError, which the tools layer reports back to the model.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import Lower, TruncMonth
from django.utils import timezone

from accounts.models import Account
from ai.context import shift_month
from transactions.models import Transaction

CENTS = Decimal('0.01')
PERCENT_PLACES = Decimal('0.1')

# RN10: both thresholds must be reached for a significant increase.
SIGNIFICANT_CHANGE_PERCENT = Decimal('20')
SIGNIFICANT_CHANGE_AMOUNT = Decimal('50.00')

# RN09: distinct months needed to treat an expense as probably recurring.
RECURRING_MIN_MONTHS = 3

MAX_CATEGORY_BREAKDOWN_LIMIT = 20
MAX_CATEGORY_CHANGES_LIMIT = 20
MAX_RECURRING_EXPENSES_LIMIT = 10
MAX_LARGEST_TRANSACTIONS_LIMIT = 10

INCOME = Transaction.TransactionType.INCOME
EXPENSE = Transaction.TransactionType.EXPENSE

INCOME_FILTER = Q(transaction_type=INCOME)
EXPENSE_FILTER = Q(transaction_type=EXPENSE)


def _cents(value):
    # Sum on SQLite is not rounded to the field places, and is None when
    # there are no rows. abs() turns a rounded -0.00 into 0.00.
    amount = (value or Decimal('0')).quantize(CENTS)
    return amount if amount else abs(amount)


def _money_text(value):
    return str(_cents(value))


def _percent_text(part, whole):
    if not whole:
        return None
    percent = (part * 100 / whole).quantize(
        PERCENT_PLACES,
        rounding=ROUND_HALF_UP,
    )
    return str(percent if percent else abs(percent))


def _check_limit(limit, maximum):
    if not 1 <= limit <= maximum:
        raise ValueError(f'limit must be between 1 and {maximum}.')


def _check_transaction_type(transaction_type):
    if transaction_type not in Transaction.TransactionType.values:
        raise ValueError('Unknown transaction type.')


def _parse_closed_month(month):
    month_start = date.fromisoformat(f'{month}-01')
    if month_start >= timezone.localdate().replace(day=1):
        raise ValueError('month must be a closed month.')
    return month_start


def _owned_transactions(user_id):
    # The related rows are checked too, so a row linked to another user's
    # account or category can never expose that data.
    return Transaction.objects.filter(
        user_id=user_id,
        account__user_id=user_id,
        category__user_id=user_id,
    )


def _period_transactions(user_id, start_date, end_date):
    # RN03: future transactions stay out, whatever end_date says.
    return _owned_transactions(user_id).filter(
        date__gte=start_date,
        date__lte=min(end_date, timezone.localdate()),
    )


def get_financial_summary(user_id, start_date, end_date):
    """Compare income and expense in a period. One query."""
    totals = _period_transactions(user_id, start_date, end_date).aggregate(
        income_total=Sum('amount', filter=INCOME_FILTER),
        expense_total=Sum('amount', filter=EXPENSE_FILTER),
        income_count=Count('pk', filter=INCOME_FILTER),
        expense_count=Count('pk', filter=EXPENSE_FILTER),
    )
    income = _cents(totals['income_total'])
    expense = _cents(totals['expense_total'])
    net_result = income - expense
    return {
        'income_total': str(income),
        'expense_total': str(expense),
        'net_result': _money_text(net_result),
        'savings_rate_percent': _percent_text(net_result, income),
        'income_count': totals['income_count'],
        'expense_count': totals['expense_count'],
    }


def get_metrics_snapshot(user_id, period_start, period_end):
    """Return the period totals stored for audit. One query."""
    return {
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        **get_financial_summary(user_id, period_start, period_end),
    }


def get_monthly_evolution(user_id, months):
    """List the last months up to the current one. One query.

    expense_change_percent is None for the first listed month, for the
    partial month (RN04) and when the previous month has no expenses.
    """
    if not 1 <= months <= settings.AI_ANALYSIS_WINDOW_MONTHS:
        raise ValueError('months is outside the analysis window.')

    today = timezone.localdate()
    current_month = today.replace(day=1)
    first_month = shift_month(current_month, 1 - months)
    # date is a DateField: TruncMonth does no time zone conversion here, and
    # rejects tzinfo. The local day only matters in timezone.localdate().
    rows = (
        _owned_transactions(user_id)
        .filter(date__gte=first_month, date__lte=today)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            income_total=Sum('amount', filter=INCOME_FILTER),
            expense_total=Sum('amount', filter=EXPENSE_FILTER),
        )
        .order_by('month')
    )
    totals_by_month = {row['month']: row for row in rows}

    evolution = []
    previous_expense = None
    for offset in range(months):
        month = shift_month(first_month, offset)
        totals = totals_by_month.get(month, {})
        income = _cents(totals.get('income_total'))
        expense = _cents(totals.get('expense_total'))
        is_partial_month = month == current_month
        expense_change_percent = None
        if previous_expense is not None and not is_partial_month:
            expense_change_percent = _percent_text(
                expense - previous_expense,
                previous_expense,
            )
        evolution.append({
            'month': month.strftime('%Y-%m'),
            'income_total': str(income),
            'expense_total': str(expense),
            'net_result': _money_text(income - expense),
            'expense_change_percent': expense_change_percent,
            'is_partial_month': is_partial_month,
        })
        previous_expense = expense
    return evolution


def get_category_breakdown(
    user_id,
    start_date,
    end_date,
    transaction_type,
    limit,
):
    """Show the largest categories and sum the others. One query.

    Reads one aggregated row per category of the user, never transactions.
    """
    _check_transaction_type(transaction_type)
    _check_limit(limit, MAX_CATEGORY_BREAKDOWN_LIMIT)

    rows = (
        _period_transactions(user_id, start_date, end_date)
        .filter(transaction_type=transaction_type)
        .values('category_id', 'category__name')
        .annotate(total=Sum('amount'), transaction_count=Count('pk'))
        .order_by()
    )
    groups = sorted(
        (
            (_cents(row['total']), row['category__name'], row)
            for row in rows
        ),
        key=lambda group: (-group[0], group[1]),
    )
    grand_total = sum((total for total, _, _ in groups), Decimal('0.00'))
    return {
        'categories': [
            {
                'category_name': name,
                'total': str(total),
                'transaction_count': row['transaction_count'],
                'share_percent': _percent_text(total, grand_total),
            }
            for total, name, row in groups[:limit]
        ],
        'others_total': _money_text(
            sum((total for total, _, _ in groups[limit:]), Decimal('0.00'))
        ),
    }


def _is_significant_increase(current_total, previous_total):
    # RN10. Without a previous expense the percentage has no base, so only
    # the amount threshold applies.
    change = current_total - previous_total
    if change < SIGNIFICANT_CHANGE_AMOUNT:
        return False
    if not previous_total:
        return True
    return change * 100 >= SIGNIFICANT_CHANGE_PERCENT * previous_total


def get_category_changes(user_id, month, limit):
    """Compare expenses of a closed month and the previous. One query.

    month is text in the AAAA-MM format. Significant increases come first,
    then the largest changes, so the limit never hides a significant
    category in favor of a common one. Reads one aggregated row per category
    of the user, never transactions.
    """
    _check_limit(limit, MAX_CATEGORY_CHANGES_LIMIT)
    month_start = _parse_closed_month(month)
    previous_start = shift_month(month_start, -1)
    next_start = shift_month(month_start, 1)

    current_filter = Q(date__gte=month_start)
    previous_filter = Q(date__lt=month_start)
    rows = (
        _owned_transactions(user_id)
        .filter(
            transaction_type=EXPENSE,
            date__gte=previous_start,
            date__lt=next_start,
        )
        .values('category_id', 'category__name')
        .annotate(
            current_total=Sum('amount', filter=current_filter),
            previous_total=Sum('amount', filter=previous_filter),
        )
        .order_by()
    )

    changes = []
    for row in rows:
        current_total = _cents(row['current_total'])
        previous_total = _cents(row['previous_total'])
        change = current_total - previous_total
        changes.append({
            'category_name': row['category__name'],
            'current_total': str(current_total),
            'previous_total': str(previous_total),
            'absolute_change': _money_text(change),
            'percent_change': _percent_text(change, previous_total),
            'is_significant': _is_significant_increase(
                current_total,
                previous_total,
            ),
        })
    changes.sort(key=lambda item: (
        not item['is_significant'],
        -abs(Decimal(item['absolute_change'])),
        item['category_name'],
    ))
    return changes[:limit]


def get_recurring_expenses(user_id, start_date, end_date, limit):
    """Find probably recurring expenses (RN09), in SQL only. One query.

    Lower only converts ASCII on SQLite, which is accepted in PRD 14.10.
    Beyond the limit, the groups with fewer months and older dates are left
    out, with no signal in the result.
    """
    _check_limit(limit, MAX_RECURRING_EXPENSES_LIMIT)

    rows = (
        _period_transactions(user_id, start_date, end_date)
        .filter(transaction_type=EXPENSE)
        .annotate(normalized_description=Lower('description'))
        .values('normalized_description', 'category_id', 'category__name')
        .annotate(
            description_label=Max('description'),
            distinct_months=Count(TruncMonth('date'), distinct=True),
            average_amount=Avg('amount'),
            last_date=Max('date'),
        )
        .filter(distinct_months__gte=RECURRING_MIN_MONTHS)
        .order_by(
            '-distinct_months',
            '-last_date',
            'normalized_description',
            'category_id',
        )[:limit]
    )
    return [
        {
            'description': row['description_label'],
            'category_name': row['category__name'],
            'distinct_months': row['distinct_months'],
            'average_amount': _money_text(row['average_amount']),
            'last_date': row['last_date'].isoformat(),
        }
        for row in rows
    ]


def get_largest_transactions(
    user_id,
    start_date,
    end_date,
    transaction_type,
    limit,
):
    """List the largest transactions of a period. One query."""
    _check_transaction_type(transaction_type)
    _check_limit(limit, MAX_LARGEST_TRANSACTIONS_LIMIT)

    transactions = (
        _period_transactions(user_id, start_date, end_date)
        .filter(transaction_type=transaction_type)
        .select_related('account', 'category')
        .order_by('-amount', '-date', '-pk')[:limit]
    )
    return [
        {
            'date': transaction.date.isoformat(),
            'description': transaction.description,
            'amount': _money_text(transaction.amount),
            'category_name': transaction.category.name,
            'account_name': transaction.account.name,
        }
        for transaction in transactions
    ]


def get_accounts_overview(user_id):
    """Show current balances, as Account.current_balance does. One query.

    RN03 makes the balance an exception: future transactions count here.
    Both sums share one join, so income and expense rows never multiply.
    """
    rows = (
        Account.objects.filter(user_id=user_id)
        .values('pk', 'name', 'account_type', 'initial_balance')
        .annotate(
            income=Sum(
                'transactions__amount',
                filter=Q(
                    transactions__user_id=user_id,
                    transactions__transaction_type=INCOME,
                ),
            ),
            expense=Sum(
                'transactions__amount',
                filter=Q(
                    transactions__user_id=user_id,
                    transactions__transaction_type=EXPENSE,
                ),
            ),
        )
        .order_by('name', 'pk')
    )

    accounts = []
    total_balance = Decimal('0.00')
    for row in rows:
        balance = _cents(
            row['initial_balance']
            + (row['income'] or Decimal('0'))
            - (row['expense'] or Decimal('0'))
        )
        total_balance += balance
        accounts.append({
            'account_name': row['name'],
            'account_type': row['account_type'],
            'current_balance': str(balance),
        })
    return {
        'accounts': accounts,
        'total_balance': _money_text(total_balance),
    }
