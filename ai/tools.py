"""Agent tools that read the run context, validate and call queries.

The owner of the data comes only from runtime.context, never from the model.
Every tool returns a dict: ToolMessage would keep an empty list as a list of
content blocks instead of the JSON text '[]'.
"""

import functools
import threading
from datetime import date
from typing import Annotated, Literal

from django.conf import settings
from django.db import connection
from langchain.tools import ToolRuntime, tool
from pydantic import Field

from ai import queries
from ai.context import AnalysisContext, shift_month

FREE_TEXT_FIELDS = ('description', 'category_name', 'account_name')

StartDate = Annotated[
    date,
    Field(description='First day, inside the analysis period.'),
]
EndDate = Annotated[
    date,
    Field(description='Last day, inside the analysis period.'),
]
TransactionKind = Annotated[
    Literal['income', 'expense'],
    Field(description='Kind of transaction to read.'),
]


def _limit_field(maximum):
    return Field(ge=1, le=maximum, description='Maximum number of items.')


class ToolArgumentError(Exception):
    """A valid argument that the run context does not allow."""

    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _require_context(runtime):
    # A run without a trusted owner is an internal failure, and not something
    # the model can correct, so it must stop the run before any query.
    context = runtime.context
    if not isinstance(context, AnalysisContext):
        raise RuntimeError('The tool has no analysis context.')
    user_id = context.user_id
    if type(user_id) is not int or user_id <= 0:
        raise RuntimeError('The analysis context has an invalid owner.')
    return context


def closes_pool_connection(func):
    """Close the Django connection when running outside the owner thread.

    ToolNode runs tools in a thread pool, and each thread gets a connection.
    The owner thread keeps its own, which may hold a transaction open.
    """

    @functools.wraps(func)
    def wrapper(*args, runtime, **kwargs):
        context = _require_context(runtime)
        try:
            return func(*args, runtime=runtime, **kwargs)
        finally:
            if threading.get_ident() != context.owner_thread_id:
                connection.close()

    return wrapper


def returns_argument_errors(func):
    """Report context errors to the model, so that it can correct the call.

    Any other exception is unexpected and must stop the run.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ToolArgumentError as error:
            return {'error': error.code, 'detail': error.detail}
        except ValueError:
            return {
                'error': 'invalid_argument',
                'detail': 'The arguments are not valid for this tool.',
            }

    return wrapper


def _check_period(context, start_date, end_date):
    if start_date > end_date:
        raise ToolArgumentError(
            'invalid_date_range',
            'start_date must not be after end_date.',
        )
    if start_date < context.period_start or end_date > context.period_end:
        raise ToolArgumentError(
            'date_out_of_period',
            'Dates must be inside the analysis period.',
        )


def _check_months(context, months):
    # get_monthly_evolution does not know the period of the run.
    current_month = context.period_end.replace(day=1)
    if shift_month(current_month, 1 - months) < context.period_start:
        raise ToolArgumentError(
            'months_out_of_period',
            'months must not go beyond the analysis period.',
        )


def _check_closed_month(context, month):
    # get_category_changes also reads the previous month and does not know
    # the period of the run, so the first month of the period is refused.
    month_start = date.fromisoformat(f'{month}-01')
    if month_start >= context.period_end.replace(day=1):
        raise ToolArgumentError(
            'month_not_closed',
            'month must be a closed month.',
        )
    if shift_month(month_start, -1) < context.period_start:
        raise ToolArgumentError(
            'month_out_of_period',
            'month and the previous month must be inside the analysis '
            'period.',
        )


def _clean_text(text):
    # Line breaks, tabs and control characters become JSON escapes, which
    # break the PII redaction and may hide a card number (docs/ia.md).
    printable = ''.join(char if char.isprintable() else ' ' for char in text)
    return ' '.join(printable.split())


def _clean_row(row):
    return {
        name: _clean_text(value) if name in FREE_TEXT_FIELDS else value
        for name, value in row.items()
    }


def _clean_rows(rows):
    return [_clean_row(row) for row in rows]


@tool
@closes_pool_connection
@returns_argument_errors
def get_financial_summary(
    start_date: StartDate,
    end_date: EndDate,
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """Compare total income and expense in a period, with the savings rate."""
    context = runtime.context
    _check_period(context, start_date, end_date)
    return queries.get_financial_summary(
        context.user_id,
        start_date,
        end_date,
    )


@tool
@closes_pool_connection
@returns_argument_errors
def get_monthly_evolution(
    months: Annotated[
        int,
        Field(
            ge=1,
            le=settings.AI_ANALYSIS_WINDOW_MONTHS,
            description='Number of months, ending in the current month.',
        ),
    ],
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """Show income and expense month by month, including empty months.

    The current month is partial: is_partial_month marks it, and it must not
    be compared as a complete month.
    """
    context = runtime.context
    _check_months(context, months)
    return {
        'months': queries.get_monthly_evolution(context.user_id, months),
    }


@tool
@closes_pool_connection
@returns_argument_errors
def get_category_breakdown(
    start_date: StartDate,
    end_date: EndDate,
    transaction_type: TransactionKind,
    limit: Annotated[
        int,
        _limit_field(queries.MAX_CATEGORY_BREAKDOWN_LIMIT),
    ],
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """Show the distribution by category; others_total sums the remainder."""
    context = runtime.context
    _check_period(context, start_date, end_date)
    breakdown = queries.get_category_breakdown(
        context.user_id,
        start_date,
        end_date,
        transaction_type,
        limit,
    )
    return {
        **breakdown,
        'categories': _clean_rows(breakdown['categories']),
    }


@tool
@closes_pool_connection
@returns_argument_errors
def get_category_changes(
    month: Annotated[
        str,
        Field(
            pattern=r'^[0-9]{4}-(0[1-9]|1[0-2])$',
            description=(
                'Closed month in the YYYY-MM format. It and the previous '
                'month must be inside the analysis period.'
            ),
        ),
    ],
    limit: Annotated[
        int,
        _limit_field(queries.MAX_CATEGORY_CHANGES_LIMIT),
    ],
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """Compare expenses by category between a closed month and the previous.

    Significant increases come first.
    """
    context = runtime.context
    _check_closed_month(context, month)
    return {
        'changes': _clean_rows(
            queries.get_category_changes(context.user_id, month, limit)
        ),
    }


@tool
@closes_pool_connection
@returns_argument_errors
def get_recurring_expenses(
    limit: Annotated[
        int,
        _limit_field(queries.MAX_RECURRING_EXPENSES_LIMIT),
    ],
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """List probably recurring expenses found in the analysis period."""
    context = runtime.context
    return {
        'expenses': _clean_rows(
            queries.get_recurring_expenses(
                context.user_id,
                context.period_start,
                context.period_end,
                limit,
            )
        ),
    }


@tool
@closes_pool_connection
@returns_argument_errors
def get_largest_transactions(
    start_date: StartDate,
    end_date: EndDate,
    transaction_type: TransactionKind,
    limit: Annotated[
        int,
        _limit_field(queries.MAX_LARGEST_TRANSACTIONS_LIMIT),
    ],
    runtime: ToolRuntime[AnalysisContext],
) -> dict:
    """List the largest transactions of a period."""
    context = runtime.context
    _check_period(context, start_date, end_date)
    return {
        'transactions': _clean_rows(
            queries.get_largest_transactions(
                context.user_id,
                start_date,
                end_date,
                transaction_type,
                limit,
            )
        ),
    }


@tool
@closes_pool_connection
@returns_argument_errors
def get_accounts_overview(runtime: ToolRuntime[AnalysisContext]) -> dict:
    """Show the current balance of each account and the total balance."""
    overview = queries.get_accounts_overview(runtime.context.user_id)
    return {
        **overview,
        'accounts': _clean_rows(overview['accounts']),
    }


FINANCIAL_TOOLS = (
    get_financial_summary,
    get_monthly_evolution,
    get_category_breakdown,
    get_category_changes,
    get_recurring_expenses,
    get_largest_transactions,
    get_accounts_overview,
)
