from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import TemplateView

from transactions.models import Transaction


class HomeView(TemplateView):
    template_name = 'home.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        accounts = list(user.accounts.all())
        totals = user.transactions.filter(
            date__year=today.year, date__month=today.month
        ).aggregate(
            income=Sum(
                'amount',
                filter=Q(transaction_type=Transaction.TransactionType.INCOME),
            ),
            expense=Sum(
                'amount',
                filter=Q(transaction_type=Transaction.TransactionType.EXPENSE),
            ),
        )
        # No SQLite o Sum volta com 15 dígitos significativos, sem arredondar
        # para as casas decimais do campo.
        month_income = (totals['income'] or Decimal('0')).quantize(
            Decimal('0.01')
        )
        month_expense = (totals['expense'] or Decimal('0')).quantize(
            Decimal('0.01')
        )
        month_result = month_income - month_expense

        context['accounts'] = accounts
        context['total_balance'] = sum(
            (account.current_balance for account in accounts), Decimal('0')
        )
        context['month_income'] = month_income
        context['month_expense'] = month_expense
        context['month_result'] = month_result
        context['month_result_abs'] = abs(month_result)
        context['latest_transactions'] = user.transactions.select_related(
            'account', 'category'
        )[:5]
        context['current_month'] = date_format(
            today, 'YEAR_MONTH_FORMAT'
        ).lower()
        return context
