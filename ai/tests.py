"""Tests of the assistant, with a fake model and no network.

Expected values are calculated by hand in the comments, never copied from
the implementation. The real API runs only in LiveAnalysisTests.
"""

import itertools
import json
import os
import subprocess
import sys
import threading
import time
import warnings
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock, skipUnless

import httpx2
import openai
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import constants as message_constants
from django.contrib.messages import get_messages
from django.db import DatabaseError, connection
from django.test import (
    Client,
    SimpleTestCase,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from langchain.agents.structured_output import (
    MultipleStructuredOutputsError,
    StructuredOutputValidationError,
)
from langchain.tools import ToolRuntime
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel,
)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from pydantic import ValidationError

from accounts.models import Account
from ai import queries, tools
from ai.agent import RunTracker, run_agent
from ai.context import (
    AnalysisContext,
    calculate_analysis_period,
    shift_month,
)
from ai.models import FinancialAnalysis
from ai.prompts import build_request_text
from ai.schemas import AnalysisOutput
from ai.services import (
    AnalysisState,
    GenerationOutcome,
    generate_analysis,
    get_dashboard_analysis_state,
    get_latest_valid_analysis,
)
from ai.validators import (
    DISCARDED_ITEM_NOTES,
    extract_tool_calls,
    extract_tool_values,
    is_invalid_output,
    validate_output,
)
from categories.models import Category
from transactions.models import Transaction

User = get_user_model()

INCOME = Transaction.TransactionType.INCOME
EXPENSE = Transaction.TransactionType.EXPENSE
Status = FinancialAnalysis.Status
ErrorCode = FinancialAnalysis.ErrorCode

# Fixed local date of the query and tool tests. With the default window of
# 6 months, the period goes from 2026-01-01 to 2026-06-15.
TODAY = date(2026, 6, 15)
PERIOD_START = date(2026, 1, 1)

FAKE_MODEL_NAME = 'fake-model'
FAKE_USAGE = {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120}

AI_SETTINGS = {
    'OPENAI_API_KEY': 'test-key-not-used',
    'AI_ANALYSIS_WINDOW_MONTHS': 6,
    'AI_ANALYSIS_MIN_TRANSACTIONS': 5,
    'AI_ANALYSIS_DAILY_LIMIT': 3,
    'AI_ANALYSIS_PENDING_TIMEOUT_MINUTES': 5,
    'AI_RUN_BUDGET_SECONDS': 120,
    'AI_MAX_MODEL_CALLS': 8,
    'AI_MAX_TOOL_CALLS': 10,
}

# Official prices of gpt-5-mini per 1 million tokens, as recorded in PRD
# 14.18 (verified on 02/11/2026). Check them again before changing models.
LIVE_INPUT_PRICE_PER_MILLION = Decimal('0.25')
LIVE_OUTPUT_PRICE_PER_MILLION = Decimal('2.00')


# 10.12.1 -----------------------------------------------------------------


class ToolCallingFakeChatModel(GenericFakeChatModel):
    """GenericFakeChatModel with bind_tools, which create_agent requires.

    It consumes an iterator, so every test creates its own instance.
    """

    def bind_tools(self, tools, **kwargs):
        return self


def fake_model(*messages):
    """Return a new fake model with a new iterator of the given messages."""
    return ToolCallingFakeChatModel(messages=iter(messages))


def ai_message(tool_calls=(), content=''):
    """Return a model message with token usage, as a provider would."""
    return AIMessage(
        content=content,
        tool_calls=[
            {
                'name': name,
                'args': args,
                'id': f'call_{index}_{name}',
                'type': 'tool_call',
            }
            for index, (name, args) in enumerate(tool_calls)
        ],
        usage_metadata=dict(FAKE_USAGE),
        response_metadata={'model_name': FAKE_MODEL_NAME},
    )


def evidence(value, source_tool='get_financial_summary', label='Valor'):
    return {'label': label, 'value': value, 'source_tool': source_tool}


def item(value, source_tool='get_financial_summary', **extra):
    return {
        'title': 'Título',
        'description': 'Descrição em português.',
        'evidence': [evidence(value, source_tool)],
        **extra,
    }


def build_output(
    main_value='3000.00',
    insight_values=('1250.00',),
    recommendation_values=('1750.00',),
    alert_values=('41.7',),
):
    return {
        'main_insight': item(main_value),
        'insights': [item(value) for value in insight_values],
        'recommendations': [item(value) for value in recommendation_values],
        'alerts': [
            item(value, severity='warning') for value in alert_values
        ],
        'data_limitations': ['O mês atual é parcial.'],
    }


def tool_message(name, data, status='success'):
    return ToolMessage(
        content=json.dumps(data),
        name=name,
        tool_call_id=f'call_{name}',
        status=status,
    )


def create_user(email):
    return User.objects.create_user(email=email, password='senha-forte-123')


def create_account(user, name, initial_balance='0.00', **kwargs):
    return Account.objects.create(
        user=user,
        name=name,
        initial_balance=Decimal(initial_balance),
        **kwargs,
    )


def create_category(user, name, category_type):
    return Category.objects.create(
        user=user,
        name=name,
        category_type=category_type,
    )


def create_transaction(account, category, amount, day, description):
    return Transaction.objects.create(
        user=account.user,
        account=account,
        category=category,
        transaction_type=category.category_type,
        amount=Decimal(amount),
        date=day,
        description=description,
    )


def build_runtime(context):
    return ToolRuntime(
        state={},
        context=context,
        config={},
        stream_writer=None,
        tool_call_id='call_test',
        store=None,
    )


def build_context(user_id, period_start=PERIOD_START, period_end=TODAY):
    return AnalysisContext(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        deadline=time.monotonic() + 60,
        owner_thread_id=threading.get_ident(),
    )


class FixedTodayMixin:
    """Freeze timezone.localdate() at TODAY for the whole test."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'django.utils.timezone.localdate',
            return_value=TODAY,
        )
        patcher.start()
        self.addCleanup(patcher.stop)


def create_financial_data(test_case):
    """Create the data of the user A, described in the tests by hand.

    Accounts: Conta corrente (1000.00) and Carteira (50.00).
    Within the period, up to TODAY (2026-06-15):
      income  3000.00 on 03-05, 04-05, 05-05 (Salário)
      expense 1200.00 on 03-10, 04-10, 05-10 (Aluguel, three spellings)
      expense  300.00 on 04-20 and 400.33 on 05-20 (Mercado)
      expense  100.00 on 05-25 and 80.00 on 06-03 (Lazer, Cinema)
    Outside the period: 10.10 on 2025-12-20, and the future rows 500.00
    income on 06-20, 999.00 on 07-01 and 20.00 Cinema on 06-25.
    """
    user = create_user('ana@finanpy.test')
    checking = create_account(user, 'Conta corrente', '1000.00')
    wallet = create_account(
        user,
        'Carteira',
        '50.00',
        account_type=Account.AccountType.WALLET,
        bank_name='Banco Secreto',
    )
    salary = create_category(user, 'Salário', INCOME)
    rent = create_category(user, 'Aluguel', EXPENSE)
    market = create_category(user, 'Mercado', EXPENSE)
    leisure = create_category(user, 'Lazer', EXPENSE)

    for month in (3, 4, 5):
        create_transaction(
            checking, salary, '3000.00', date(2026, month, 5), 'Salário',
        )
    create_transaction(
        checking, rent, '1200.00', date(2026, 3, 10), 'Aluguel',
    )
    create_transaction(
        checking, rent, '1200.00', date(2026, 4, 10), 'aluguel',
    )
    create_transaction(
        checking, rent, '1200.00', date(2026, 5, 10), 'ALUGUEL',
    )
    create_transaction(
        checking, market, '300.00', date(2026, 4, 20), 'Supermercado',
    )
    create_transaction(
        wallet, market, '400.33', date(2026, 5, 20), 'Supermercado',
    )
    create_transaction(
        wallet, leisure, '100.00', date(2026, 5, 25), 'Cinema',
    )
    create_transaction(
        checking, leisure, '80.00', date(2026, 6, 3), 'Cinema',
    )
    create_transaction(
        checking, market, '10.10', date(2025, 12, 20), 'Antigo',
    )
    create_transaction(
        checking, salary, '500.00', date(2026, 6, 20), 'Bônus',
    )
    create_transaction(
        checking, market, '999.00', date(2026, 7, 1), 'Futuro',
    )
    create_transaction(
        checking, leisure, '20.00', date(2026, 6, 25), 'Cinema',
    )

    # The user B has data in the same months, which must never appear.
    other = create_user('bruno@finanpy.test')
    other_account = create_account(other, 'Conta corrente', '7777.00')
    other_category = create_category(other, 'Mercado', EXPENSE)
    for month in (3, 4, 5):
        create_transaction(
            other_account,
            other_category,
            '5555.55',
            date(2026, month, 12),
            'Supermercado',
        )

    test_case.user = user
    test_case.other = other
    test_case.checking = checking
    test_case.wallet = wallet


# 10.12.2 and 10.12.3 -------------------------------------------------------


class QueriesTests(FixedTodayMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        create_financial_data(cls)

    def test_financial_summary_leaves_out_future_and_old_rows(self):
        # Income 3 x 3000.00 = 9000.00. Expense 3 x 1200.00 + 300.00 +
        # 400.33 + 100.00 + 80.00 = 4480.33. Net 4519.67, and the savings
        # rate is 4519.67 / 9000.00 = 50.2%. end_date after TODAY does not
        # bring the rows of 06-20, 06-25 and 07-01 (RN03).
        summary = queries.get_financial_summary(
            self.user.pk,
            PERIOD_START,
            date(2026, 7, 31),
        )

        self.assertEqual(summary, {
            'income_total': '9000.00',
            'expense_total': '4480.33',
            'net_result': '4519.67',
            'savings_rate_percent': '50.2',
            'income_count': 3,
            'expense_count': 7,
        })

    def test_financial_summary_of_a_single_month(self):
        # May: income 3000.00; expense 1200.00 + 400.33 + 100.00 = 1700.33.
        # Net 1299.67, savings rate 43.3%.
        summary = queries.get_financial_summary(
            self.user.pk,
            date(2026, 5, 1),
            date(2026, 5, 31),
        )

        self.assertEqual(summary['income_total'], '3000.00')
        self.assertEqual(summary['expense_total'], '1700.33')
        self.assertEqual(summary['net_result'], '1299.67')
        self.assertEqual(summary['savings_rate_percent'], '43.3')

    def test_financial_summary_without_income_has_no_savings_rate(self):
        # June up to TODAY: only the expense of 80.00.
        summary = queries.get_financial_summary(
            self.user.pk,
            date(2026, 6, 1),
            date(2026, 6, 30),
        )

        self.assertEqual(summary, {
            'income_total': '0.00',
            'expense_total': '80.00',
            'net_result': '-80.00',
            'savings_rate_percent': None,
            'income_count': 0,
            'expense_count': 1,
        })

    def test_financial_summary_of_a_user_without_data(self):
        user = create_user('vazio@finanpy.test')

        summary = queries.get_financial_summary(user.pk, PERIOD_START, TODAY)

        self.assertEqual(summary, {
            'income_total': '0.00',
            'expense_total': '0.00',
            'net_result': '0.00',
            'savings_rate_percent': None,
            'income_count': 0,
            'expense_count': 0,
        })

    def test_metrics_snapshot_adds_the_period(self):
        snapshot = queries.get_metrics_snapshot(
            self.user.pk,
            PERIOD_START,
            TODAY,
        )

        self.assertEqual(snapshot['period_start'], '2026-01-01')
        self.assertEqual(snapshot['period_end'], '2026-06-15')
        self.assertEqual(snapshot['income_total'], '9000.00')
        self.assertEqual(snapshot['expense_count'], 7)

    def test_monthly_evolution_lists_empty_and_partial_months(self):
        # Jan and Feb have no rows. Expense changes: Apr (1500.00 vs
        # 1200.00) = 25.0%; May (1700.33 vs 1500.00) = 13.4%. Mar has no
        # base (0.00 in Feb) and June is partial (RN04), so both are None.
        evolution = queries.get_monthly_evolution(self.user.pk, 6)

        self.assertEqual(evolution, [
            {
                'month': '2026-01',
                'income_total': '0.00',
                'expense_total': '0.00',
                'net_result': '0.00',
                'expense_change_percent': None,
                'is_partial_month': False,
            },
            {
                'month': '2026-02',
                'income_total': '0.00',
                'expense_total': '0.00',
                'net_result': '0.00',
                'expense_change_percent': None,
                'is_partial_month': False,
            },
            {
                'month': '2026-03',
                'income_total': '3000.00',
                'expense_total': '1200.00',
                'net_result': '1800.00',
                'expense_change_percent': None,
                'is_partial_month': False,
            },
            {
                'month': '2026-04',
                'income_total': '3000.00',
                'expense_total': '1500.00',
                'net_result': '1500.00',
                'expense_change_percent': '25.0',
                'is_partial_month': False,
            },
            {
                'month': '2026-05',
                'income_total': '3000.00',
                'expense_total': '1700.33',
                'net_result': '1299.67',
                'expense_change_percent': '13.4',
                'is_partial_month': False,
            },
            {
                'month': '2026-06',
                'income_total': '0.00',
                'expense_total': '80.00',
                'net_result': '-80.00',
                'expense_change_percent': None,
                'is_partial_month': True,
            },
        ])

    def test_monthly_evolution_of_one_month_is_the_partial_month(self):
        evolution = queries.get_monthly_evolution(self.user.pk, 1)

        self.assertEqual(len(evolution), 1)
        self.assertEqual(evolution[0]['month'], '2026-06')
        self.assertTrue(evolution[0]['is_partial_month'])

    def test_monthly_evolution_rejects_months_outside_the_window(self):
        for months in (0, 7):
            with self.subTest(months=months):
                with self.assertRaises(ValueError):
                    queries.get_monthly_evolution(self.user.pk, months)

    def test_category_breakdown_sums_the_categories_beyond_the_limit(self):
        # Aluguel 3600.00 (3), Mercado 700.33 (2), Lazer 180.00 (2), total
        # 4480.33. Shares: 3600.00 / 4480.33 = 80.4%, 700.33 / 4480.33 =
        # 15.6%. Lazer goes to others_total.
        breakdown = queries.get_category_breakdown(
            self.user.pk,
            PERIOD_START,
            TODAY,
            EXPENSE,
            2,
        )

        self.assertEqual(breakdown, {
            'categories': [
                {
                    'category_name': 'Aluguel',
                    'total': '3600.00',
                    'transaction_count': 3,
                    'share_percent': '80.4',
                },
                {
                    'category_name': 'Mercado',
                    'total': '700.33',
                    'transaction_count': 2,
                    'share_percent': '15.6',
                },
            ],
            'others_total': '180.00',
        })

    def test_category_breakdown_of_income_without_others(self):
        breakdown = queries.get_category_breakdown(
            self.user.pk,
            PERIOD_START,
            TODAY,
            INCOME,
            20,
        )

        self.assertEqual(breakdown, {
            'categories': [
                {
                    'category_name': 'Salário',
                    'total': '9000.00',
                    'transaction_count': 3,
                    'share_percent': '100.0',
                },
            ],
            'others_total': '0.00',
        })

    def test_category_breakdown_rejects_invalid_arguments(self):
        cases = (
            ('transfer', 5),
            (EXPENSE, 0),
            (EXPENSE, queries.MAX_CATEGORY_BREAKDOWN_LIMIT + 1),
        )
        for transaction_type, limit in cases:
            with self.subTest(transaction_type=transaction_type, limit=limit):
                with self.assertRaises(ValueError):
                    queries.get_category_breakdown(
                        self.user.pk,
                        PERIOD_START,
                        TODAY,
                        transaction_type,
                        limit,
                    )

    def test_category_changes_compares_a_closed_month(self):
        # May vs April. Mercado: 400.33 - 300.00 = 100.33, 33.4%, and both
        # thresholds of RN10 are reached. Lazer: 100.00 - 0.00, no
        # percentage, significant by the amount. Aluguel: no change.
        changes = queries.get_category_changes(self.user.pk, '2026-05', 10)

        self.assertEqual(changes, [
            {
                'category_name': 'Mercado',
                'current_total': '400.33',
                'previous_total': '300.00',
                'absolute_change': '100.33',
                'percent_change': '33.4',
                'is_significant': True,
            },
            {
                'category_name': 'Lazer',
                'current_total': '100.00',
                'previous_total': '0.00',
                'absolute_change': '100.00',
                'percent_change': None,
                'is_significant': True,
            },
            {
                'category_name': 'Aluguel',
                'current_total': '1200.00',
                'previous_total': '1200.00',
                'absolute_change': '0.00',
                'percent_change': '0.0',
                'is_significant': False,
            },
        ])

    def test_category_changes_limit_keeps_significant_first(self):
        changes = queries.get_category_changes(self.user.pk, '2026-05', 1)

        self.assertEqual(
            [change['category_name'] for change in changes],
            ['Mercado'],
        )

    def test_category_changes_rejects_open_and_invalid_months(self):
        cases = (
            ('2026-06', 10),
            ('2026-08', 10),
            ('2026-13', 10),
            ('maio', 10),
            ('2026-05', 0),
            ('2026-05', queries.MAX_CATEGORY_CHANGES_LIMIT + 1),
        )
        for month, limit in cases:
            with self.subTest(month=month, limit=limit):
                with self.assertRaises(ValueError):
                    queries.get_category_changes(self.user.pk, month, limit)

    def test_significant_increase_thresholds(self):
        # RN10: at least 20% and at least 50.00. Without a previous expense,
        # only the amount counts.
        cases = (
            ('300.00', '250.00', True),
            ('250.00', '200.00', True),
            ('240.00', '200.00', False),
            ('1100.00', '1000.00', False),
            ('60.00', '0.00', True),
            ('49.99', '0.00', False),
            ('100.00', '200.00', False),
        )
        for current, previous, expected in cases:
            with self.subTest(current=current, previous=previous):
                self.assertIs(
                    queries._is_significant_increase(
                        Decimal(current),
                        Decimal(previous),
                    ),
                    expected,
                )

    def test_recurring_expenses_ignore_case_and_future_rows(self):
        # Aluguel appears in 3 months with 3 spellings, and Max() of the
        # text is the lower case one. Cinema has 2 months up to TODAY: the
        # future row of 06-25 would be the third (RN03). Supermercado has 2.
        recurring = queries.get_recurring_expenses(
            self.user.pk,
            PERIOD_START,
            date(2026, 12, 31),
            10,
        )

        self.assertEqual(recurring, [
            {
                'description': 'aluguel',
                'category_name': 'Aluguel',
                'distinct_months': 3,
                'average_amount': '1200.00',
                'last_date': '2026-05-10',
            },
        ])

    def test_recurring_expenses_count_distinct_months(self):
        # Two rows in the same month count once: only April and May.
        market = Category.objects.get(user=self.user, name='Mercado')
        create_transaction(
            self.checking, market, '50.00', date(2026, 5, 2), 'Supermercado',
        )

        recurring = queries.get_recurring_expenses(
            self.user.pk,
            PERIOD_START,
            TODAY,
            10,
        )

        self.assertEqual(
            [row['description'] for row in recurring],
            ['aluguel'],
        )

    def test_recurring_expenses_reject_invalid_limits(self):
        for limit in (0, queries.MAX_RECURRING_EXPENSES_LIMIT + 1):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    queries.get_recurring_expenses(
                        self.user.pk,
                        PERIOD_START,
                        TODAY,
                        limit,
                    )

    def test_largest_transactions_order_and_future_rows(self):
        # Three rents of 1200.00, the newest first, then 400.33. The future
        # 999.00 of 07-01 stays out.
        largest = queries.get_largest_transactions(
            self.user.pk,
            PERIOD_START,
            date(2026, 12, 31),
            EXPENSE,
            4,
        )

        self.assertEqual(largest, [
            {
                'date': '2026-05-10',
                'description': 'ALUGUEL',
                'amount': '1200.00',
                'category_name': 'Aluguel',
                'account_name': 'Conta corrente',
            },
            {
                'date': '2026-04-10',
                'description': 'aluguel',
                'amount': '1200.00',
                'category_name': 'Aluguel',
                'account_name': 'Conta corrente',
            },
            {
                'date': '2026-03-10',
                'description': 'Aluguel',
                'amount': '1200.00',
                'category_name': 'Aluguel',
                'account_name': 'Conta corrente',
            },
            {
                'date': '2026-05-20',
                'description': 'Supermercado',
                'amount': '400.33',
                'category_name': 'Mercado',
                'account_name': 'Carteira',
            },
        ])

    def test_largest_transactions_of_income(self):
        largest = queries.get_largest_transactions(
            self.user.pk,
            PERIOD_START,
            date(2026, 12, 31),
            INCOME,
            10,
        )

        self.assertEqual(
            [(row['date'], row['amount']) for row in largest],
            [
                ('2026-05-05', '3000.00'),
                ('2026-04-05', '3000.00'),
                ('2026-03-05', '3000.00'),
            ],
        )

    def test_largest_transactions_reject_invalid_arguments(self):
        cases = (
            ('transfer', 5),
            (EXPENSE, 0),
            (EXPENSE, queries.MAX_LARGEST_TRANSACTIONS_LIMIT + 1),
        )
        for transaction_type, limit in cases:
            with self.subTest(transaction_type=transaction_type, limit=limit):
                with self.assertRaises(ValueError):
                    queries.get_largest_transactions(
                        self.user.pk,
                        PERIOD_START,
                        TODAY,
                        transaction_type,
                        limit,
                    )

    def test_accounts_overview_includes_future_rows(self):
        # Carteira: 50.00 - 400.33 - 100.00 = -450.33.
        # Conta corrente: 1000.00 + 9000.00 + 500.00 (future) - 3600.00 -
        # 300.00 - 80.00 - 10.10 - 999.00 - 20.00 = 5490.90.
        # Total: 5490.90 - 450.33 = 5040.57. bank_name is never returned.
        overview = queries.get_accounts_overview(self.user.pk)

        self.assertEqual(overview, {
            'accounts': [
                {
                    'account_name': 'Carteira',
                    'account_type': 'wallet',
                    'current_balance': '-450.33',
                },
                {
                    'account_name': 'Conta corrente',
                    'account_type': 'checking',
                    'current_balance': '5490.90',
                },
            ],
            'total_balance': '5040.57',
        })

    def test_accounts_overview_matches_current_balance(self):
        empty = create_account(self.user, 'Poupança', '12.34')
        overview = queries.get_accounts_overview(self.user.pk)
        balances = {
            row['account_name']: row['current_balance']
            for row in overview['accounts']
        }

        accounts = Account.objects.filter(user=self.user)
        self.assertEqual(len(balances), accounts.count())
        for account in accounts:
            with self.subTest(account=account.name):
                self.assertEqual(
                    balances[account.name],
                    str(account.current_balance),
                )
        self.assertEqual(balances[empty.name], '12.34')
        self.assertEqual(
            Decimal(overview['total_balance']),
            sum(account.current_balance for account in accounts),
        )

    def test_accounts_overview_of_a_user_without_accounts(self):
        user = create_user('semcontas@finanpy.test')

        self.assertEqual(
            queries.get_accounts_overview(user.pk),
            {'accounts': [], 'total_balance': '0.00'},
        )


# 10.12.4 ---------------------------------------------------------------


class QueryCountTests(FixedTodayMixin, TestCase):
    """Every query function runs one query, whatever the volume of data."""

    @classmethod
    def setUpTestData(cls):
        cls.small_user = create_user('pouco@finanpy.test')
        account = create_account(cls.small_user, 'Conta', '10.00')
        category = create_category(cls.small_user, 'Mercado', EXPENSE)
        create_transaction(
            account, category, '10.00', date(2026, 5, 3), 'Feira',
        )

        cls.large_user = create_user('muito@finanpy.test')
        accounts = [
            create_account(cls.large_user, f'Conta {index}', '100.00')
            for index in range(5)
        ]
        categories = [
            create_category(cls.large_user, f'Saída {index}', EXPENSE)
            for index in range(8)
        ] + [
            create_category(cls.large_user, f'Entrada {index}', INCOME)
            for index in range(3)
        ]
        rows = []
        for index in range(300):
            category = categories[index % len(categories)]
            rows.append(Transaction(
                user=cls.large_user,
                account=accounts[index % len(accounts)],
                category=category,
                transaction_type=category.category_type,
                amount=Decimal('10.00') + index,
                date=date(2026, 1 + index % 6, 1 + index % 15),
                description=f'Lançamento {index % 12}',
            ))
        Transaction.objects.bulk_create(rows)

    def query_calls(self):
        return (
            ('get_financial_summary', lambda user_id: (
                queries.get_financial_summary(user_id, PERIOD_START, TODAY)
            )),
            ('get_metrics_snapshot', lambda user_id: (
                queries.get_metrics_snapshot(user_id, PERIOD_START, TODAY)
            )),
            ('get_monthly_evolution', lambda user_id: (
                queries.get_monthly_evolution(user_id, 6)
            )),
            ('get_category_breakdown', lambda user_id: (
                queries.get_category_breakdown(
                    user_id, PERIOD_START, TODAY, EXPENSE, 20,
                )
            )),
            ('get_category_changes', lambda user_id: (
                queries.get_category_changes(user_id, '2026-05', 20)
            )),
            ('get_recurring_expenses', lambda user_id: (
                queries.get_recurring_expenses(
                    user_id, PERIOD_START, TODAY, 10,
                )
            )),
            ('get_largest_transactions', lambda user_id: (
                queries.get_largest_transactions(
                    user_id, PERIOD_START, TODAY, EXPENSE, 10,
                )
            )),
            ('get_accounts_overview', queries.get_accounts_overview),
        )

    def test_queries_run_one_query_for_any_volume(self):
        for name, call in self.query_calls():
            for user in (self.small_user, self.large_user):
                with self.subTest(query=name, user=user.email):
                    with self.assertNumQueries(1):
                        call(user.pk)

    def test_large_volume_returns_data(self):
        # Guards the test above against a large user with no rows.
        summary = queries.get_financial_summary(
            self.large_user.pk,
            PERIOD_START,
            TODAY,
        )

        self.assertEqual(
            summary['income_count'] + summary['expense_count'],
            300,
        )
        self.assertEqual(
            len(queries.get_accounts_overview(self.large_user.pk)['accounts']),
            5,
        )

    def test_tools_run_one_query_for_any_volume(self):
        calls = (
            (tools.get_financial_summary, {
                'start_date': '2026-01-01', 'end_date': '2026-06-15',
            }),
            (tools.get_monthly_evolution, {'months': 6}),
            (tools.get_category_breakdown, {
                'start_date': '2026-01-01',
                'end_date': '2026-06-15',
                'transaction_type': 'expense',
                'limit': 20,
            }),
            (tools.get_category_changes, {'month': '2026-05', 'limit': 20}),
            (tools.get_recurring_expenses, {'limit': 10}),
            (tools.get_largest_transactions, {
                'start_date': '2026-01-01',
                'end_date': '2026-06-15',
                'transaction_type': 'expense',
                'limit': 10,
            }),
            (tools.get_accounts_overview, {}),
        )
        for agent_tool, args in calls:
            for user in (self.small_user, self.large_user):
                runtime = build_runtime(build_context(user.pk))
                with self.subTest(tool=agent_tool.name, user=user.email):
                    with self.assertNumQueries(1):
                        agent_tool.invoke({**args, 'runtime': runtime})


# 10.12.5 ---------------------------------------------------------------


class ToolsTests(FixedTodayMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        create_financial_data(cls)

    def setUp(self):
        super().setUp()
        self.runtime = build_runtime(build_context(self.user.pk))

    def invoke(self, agent_tool, **args):
        return agent_tool.invoke({**args, 'runtime': self.runtime})

    def test_model_never_sees_the_owner_or_the_runtime(self):
        for agent_tool in tools.FINANCIAL_TOOLS:
            with self.subTest(tool=agent_tool.name):
                properties = agent_tool.tool_call_schema.model_json_schema()[
                    'properties'
                ]
                self.assertNotIn('runtime', properties)
                self.assertNotIn('user_id', properties)
                self.assertNotIn('user', properties)

    def test_valid_calls_return_the_query_data(self):
        self.assertEqual(
            self.invoke(
                tools.get_financial_summary,
                start_date='2026-01-01',
                end_date='2026-06-15',
            ),
            queries.get_financial_summary(self.user.pk, PERIOD_START, TODAY),
        )
        evolution = self.invoke(tools.get_monthly_evolution, months=6)
        self.assertEqual(len(evolution['months']), 6)
        breakdown = self.invoke(
            tools.get_category_breakdown,
            start_date='2026-01-01',
            end_date='2026-06-15',
            transaction_type='expense',
            limit=2,
        )
        self.assertEqual(breakdown['others_total'], '180.00')
        changes = self.invoke(
            tools.get_category_changes,
            month='2026-05',
            limit=10,
        )
        self.assertEqual(changes['changes'][0]['category_name'], 'Mercado')
        recurring = self.invoke(tools.get_recurring_expenses, limit=10)
        self.assertEqual(recurring['expenses'][0]['distinct_months'], 3)
        largest = self.invoke(
            tools.get_largest_transactions,
            start_date='2026-05-01',
            end_date='2026-05-31',
            transaction_type='expense',
            limit=1,
        )
        self.assertEqual(largest['transactions'][0]['amount'], '1200.00')
        overview = self.invoke(tools.get_accounts_overview)
        self.assertEqual(overview['total_balance'], '5040.57')

    def test_empty_results_are_dicts(self):
        user = create_user('vazio@finanpy.test')
        self.runtime = build_runtime(build_context(user.pk))

        self.assertEqual(
            self.invoke(tools.get_recurring_expenses, limit=10),
            {'expenses': []},
        )

    def test_dates_outside_the_period_return_an_error(self):
        cases = (
            ('2025-12-31', '2026-06-15', 'date_out_of_period'),
            ('2026-01-01', '2026-06-16', 'date_out_of_period'),
            ('2026-05-31', '2026-05-01', 'invalid_date_range'),
        )
        for start_date, end_date, error in cases:
            with self.subTest(start_date=start_date, end_date=end_date):
                result = self.invoke(
                    tools.get_financial_summary,
                    start_date=start_date,
                    end_date=end_date,
                )
                self.assertEqual(result['error'], error)
                self.assertIn('detail', result)
                self.assertEqual(set(result), {'error', 'detail'})

    def test_other_tools_check_the_period(self):
        for agent_tool in (
            tools.get_category_breakdown,
            tools.get_largest_transactions,
        ):
            with self.subTest(tool=agent_tool.name):
                result = self.invoke(
                    agent_tool,
                    start_date='2025-06-01',
                    end_date='2026-06-15',
                    transaction_type='expense',
                    limit=5,
                )
                self.assertEqual(result['error'], 'date_out_of_period')

    def test_months_beyond_the_period_return_an_error(self):
        self.runtime = build_runtime(
            build_context(self.user.pk, period_start=date(2026, 4, 1)),
        )

        self.assertEqual(
            len(self.invoke(tools.get_monthly_evolution, months=3)['months']),
            3,
        )
        result = self.invoke(tools.get_monthly_evolution, months=4)
        self.assertEqual(result['error'], 'months_out_of_period')

    def test_category_changes_needs_closed_months_inside_the_period(self):
        cases = (
            ('2026-06', 'month_not_closed'),
            ('2026-09', 'month_not_closed'),
            ('2026-01', 'month_out_of_period'),
        )
        for month, error in cases:
            with self.subTest(month=month):
                result = self.invoke(
                    tools.get_category_changes,
                    month=month,
                    limit=5,
                )
                self.assertEqual(result['error'], error)

        result = self.invoke(
            tools.get_category_changes,
            month='2026-02',
            limit=5,
        )
        self.assertEqual(result, {'changes': []})

    def test_limits_above_the_maximum_are_rejected_by_the_schema(self):
        # Inside the agent, ToolNode returns these errors to the model.
        cases = (
            (tools.get_category_breakdown, {
                'start_date': '2026-01-01',
                'end_date': '2026-06-15',
                'transaction_type': 'expense',
                'limit': queries.MAX_CATEGORY_BREAKDOWN_LIMIT + 1,
            }),
            (tools.get_category_changes, {
                'month': '2026-05',
                'limit': queries.MAX_CATEGORY_CHANGES_LIMIT + 1,
            }),
            (tools.get_recurring_expenses, {
                'limit': queries.MAX_RECURRING_EXPENSES_LIMIT + 1,
            }),
            (tools.get_largest_transactions, {
                'start_date': '2026-01-01',
                'end_date': '2026-06-15',
                'transaction_type': 'expense',
                'limit': queries.MAX_LARGEST_TRANSACTIONS_LIMIT + 1,
            }),
            (tools.get_monthly_evolution, {'months': 7}),
            (tools.get_category_changes, {'month': '2026-5', 'limit': 5}),
            (tools.get_largest_transactions, {
                'start_date': '2026-01-01',
                'end_date': '2026-06-15',
                'transaction_type': 'transfer',
                'limit': 5,
            }),
        )
        for agent_tool, args in cases:
            with self.subTest(tool=agent_tool.name, args=args):
                with self.assertRaises(ValidationError):
                    self.invoke(agent_tool, **args)

    def test_limits_past_the_schema_return_an_error(self):
        # A second barrier: the query refuses the value, and the tool turns
        # the ValueError into an error the model can correct.
        result = tools.get_category_breakdown.func(
            start_date=PERIOD_START,
            end_date=TODAY,
            transaction_type='expense',
            limit=queries.MAX_CATEGORY_BREAKDOWN_LIMIT + 1,
            runtime=self.runtime,
        )

        self.assertEqual(result, {
            'error': 'invalid_argument',
            'detail': 'The arguments are not valid for this tool.',
        })

    def test_tool_without_analysis_context_stops_the_run(self):
        runtime = build_runtime({'user_id': self.user.pk})

        # Pydantic warns about the wrong context type before the check.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with self.assertRaises(RuntimeError):
                tools.get_accounts_overview.invoke({'runtime': runtime})

    def test_tool_with_invalid_owner_stops_the_run(self):
        for user_id in (0, -1, str(self.user.pk), True):
            with self.subTest(user_id=user_id):
                context = AnalysisContext(
                    user_id=user_id,
                    period_start=PERIOD_START,
                    period_end=TODAY,
                    deadline=time.monotonic() + 60,
                    owner_thread_id=threading.get_ident(),
                )
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    with self.assertRaises(RuntimeError):
                        tools.get_accounts_overview.invoke(
                            {'runtime': build_runtime(context)},
                        )

    def test_free_text_is_flattened(self):
        market = Category.objects.get(user=self.user, name='Mercado')
        create_transaction(
            self.checking,
            market,
            '5000.00',
            date(2026, 6, 1),
            'Linha\nquebrada\tcom\x00controle',
        )

        result = self.invoke(
            tools.get_largest_transactions,
            start_date='2026-06-01',
            end_date='2026-06-15',
            transaction_type='expense',
            limit=1,
        )

        self.assertEqual(
            result['transactions'][0]['description'],
            'Linha quebrada com controle',
        )

    def test_unexpected_errors_are_not_hidden(self):
        with mock.patch.object(
            queries,
            'get_financial_summary',
            side_effect=DatabaseError('falha'),
        ):
            with self.assertRaises(DatabaseError):
                self.invoke(
                    tools.get_financial_summary,
                    start_date='2026-01-01',
                    end_date='2026-06-15',
                )

    def test_pool_thread_closes_its_connection(self):
        # The owner thread is another one, as in the ToolNode pool.
        context = AnalysisContext(
            user_id=self.user.pk,
            period_start=PERIOD_START,
            period_end=TODAY,
            deadline=time.monotonic() + 60,
            owner_thread_id=threading.get_ident() + 1,
        )
        with mock.patch('ai.tools.connection') as connection:
            tools.get_recurring_expenses.invoke(
                {'limit': 5, 'runtime': build_runtime(context)},
            )
        connection.close.assert_called_once_with()

    def test_owner_thread_keeps_its_connection(self):
        with mock.patch('ai.tools.connection') as connection:
            self.invoke(tools.get_recurring_expenses, limit=5)
        connection.close.assert_not_called()


class ContextAndPromptTests(TestCase):
    def test_shift_month_crosses_years(self):
        self.assertEqual(shift_month(date(2026, 1, 1), -1), date(2025, 12, 1))
        self.assertEqual(shift_month(date(2026, 12, 1), 1), date(2027, 1, 1))
        self.assertEqual(shift_month(date(2026, 6, 1), -17), date(2025, 1, 1))

    def test_analysis_period_follows_rn02(self):
        with mock.patch(
            'django.utils.timezone.localdate',
            return_value=date(2026, 2, 10),
        ):
            self.assertEqual(
                calculate_analysis_period(),
                (date(2025, 9, 1), date(2026, 2, 10)),
            )

    def test_request_text_has_no_user_data(self):
        context = build_context(123456)
        text = build_request_text(context)

        self.assertIn('2026-01-01 to 2026-06-15', text)
        self.assertIn('Current partial month: 2026-06.', text)
        self.assertIn('get_category_changes: 2026-02 to 2026-05.', text)
        self.assertNotIn('123456', text)

    def test_request_text_without_comparable_month(self):
        context = build_context(
            1,
            period_start=date(2026, 6, 1),
            period_end=TODAY,
        )

        self.assertIn(
            'get_category_changes: none.',
            build_request_text(context),
        )


# 10.12.8 ---------------------------------------------------------------


SUMMARY_DATA = {
    'income_total': '3000.00',
    'expense_total': '1750.00',
    'net_result': '1250.00',
    'savings_rate_percent': '41.7',
    'income_count': 1,
    'expense_count': 4,
}


class EvidenceValidationTests(TestCase):
    def setUp(self):
        self.messages = [
            HumanMessage(content='Analise.'),
            tool_message('get_financial_summary', SUMMARY_DATA),
            tool_message('get_largest_transactions', {'transactions': [{
                'date': '2026-05-10',
                'description': '999.99',
                'amount': '1200.00',
                'category_name': 'Aluguel',
                'account_name': 'Conta corrente',
            }]}),
            tool_message('get_monthly_evolution', {'months': [{
                'month': '2026-06',
                'is_partial_month': True,
            }]}),
        ]

    def test_valid_output_is_kept_whole(self):
        output = build_output()

        check = validate_output(output, self.messages)

        self.assertTrue(check.is_verified)
        self.assertEqual(check.content, {
            'main_insight': output['main_insight'],
            'insights': output['insights'],
            'recommendations': output['recommendations'],
            'alerts': output['alerts'],
            'data_limitations': ['O mês atual é parcial.'],
        })

    def test_values_are_normalized(self):
        output = build_output(main_value=' 3000.0 ')
        output['insights'] = [item('aluguel', 'get_largest_transactions')]
        output['alerts'] = [item(
            'TRUE',
            'get_monthly_evolution',
            severity='info',
        )]

        check = validate_output(output, self.messages)

        self.assertTrue(check.is_verified)
        self.assertEqual(len(check.content['insights']), 1)
        self.assertEqual(len(check.content['alerts']), 1)

    def test_invented_main_insight_rejects_the_analysis(self):
        check = validate_output(
            build_output(main_value='3500.00'),
            self.messages,
        )

        self.assertFalse(check.is_verified)
        self.assertEqual(check.content, {})

    def test_evidence_from_another_tool_is_not_accepted(self):
        output = build_output()
        output['main_insight']['evidence'][0]['source_tool'] = (
            'get_accounts_overview'
        )

        self.assertFalse(validate_output(output, self.messages).is_verified)

    def test_invented_items_are_discarded_and_recorded(self):
        output = build_output(
            insight_values=('1250.00', '8888.88'),
            recommendation_values=('1750.00', '4.2'),
            alert_values=('77.7',),
        )

        check = validate_output(output, self.messages)

        self.assertTrue(check.is_verified)
        self.assertEqual(check.content['insights'], [output['insights'][0]])
        self.assertEqual(
            check.content['recommendations'],
            [output['recommendations'][0]],
        )
        self.assertEqual(check.content['alerts'], [])
        self.assertEqual(check.content['data_limitations'], [
            'O mês atual é parcial.',
            DISCARDED_ITEM_NOTES['insights'],
            DISCARDED_ITEM_NOTES['recommendations'],
            DISCARDED_ITEM_NOTES['alerts'],
        ])
        # The discarded text never reaches the record.
        self.assertNotIn('8888.88', json.dumps(check.content))

    def test_item_with_one_invented_evidence_is_discarded(self):
        output = build_output()
        output['insights'][0]['evidence'].append(evidence('1.00'))

        check = validate_output(output, self.messages)

        self.assertEqual(check.content['insights'], [])

    def test_no_verified_recommendation_rejects_the_analysis(self):
        check = validate_output(
            build_output(recommendation_values=('123.45',)),
            self.messages,
        )

        self.assertFalse(check.is_verified)

    def test_kinds_of_values_never_match_by_accident(self):
        # A count is not money, a description is not an amount and an
        # error result is not evidence.
        messages = [
            *self.messages,
            tool_message('get_category_changes', {
                'error': 'month_not_closed',
                'detail': '2026-06',
            }),
        ]
        cases = (
            ('1.00', 'get_financial_summary'),
            ('4', 'get_largest_transactions'),
            ('999.99', 'get_largest_transactions'),
            ('month_not_closed', 'get_category_changes'),
            ('R$ 3.000,00', 'get_financial_summary'),
            ('', 'get_financial_summary'),
        )
        for value, source_tool in cases:
            with self.subTest(value=value):
                output = build_output()
                output['main_insight'] = item(value, source_tool)
                self.assertFalse(
                    validate_output(output, messages).is_verified,
                )

        output = build_output()
        output['main_insight'] = item('4')
        self.assertTrue(validate_output(output, messages).is_verified)

    def test_errors_and_unreadable_results_are_not_evidence(self):
        messages = [
            tool_message('get_financial_summary', SUMMARY_DATA, 'error'),
            ToolMessage(
                content='not json',
                name='get_accounts_overview',
                tool_call_id='call_x',
            ),
            ToolMessage(
                content=json.dumps(build_output()),
                name='AnalysisOutput',
                tool_call_id='call_y',
            ),
            ToolMessage(
                content=[{'type': 'text', 'text': '{}'}],
                name='get_monthly_evolution',
                tool_call_id='call_z',
            ),
        ]

        self.assertEqual(extract_tool_values(messages), {})

    def test_tool_calls_leave_the_output_tool_out(self):
        messages = [
            HumanMessage(content='Analise.'),
            ai_message([
                ('get_financial_summary', {'start_date': '2026-01-01'}),
                ('get_accounts_overview', {}),
            ]),
            ai_message([('AnalysisOutput', build_output())]),
        ]

        self.assertEqual(extract_tool_calls(messages), [
            {
                'name': 'get_financial_summary',
                'args': {'start_date': '2026-01-01'},
            },
            {'name': 'get_accounts_overview', 'args': {}},
        ])

    def test_invalid_output_detection(self):
        refused = ToolMessage(
            content='Error: 1 validation error\n Please fix your mistakes.',
            name='AnalysisOutput',
            tool_call_id='call_1',
        )
        blocked = ToolMessage(
            content='Tool call limit exceeded.',
            name='AnalysisOutput',
            tool_call_id='call_1',
            status='error',
        )
        output_call = ai_message([('AnalysisOutput', {})])
        data_call = ai_message([('get_accounts_overview', {})])
        limit_message = AIMessage(content='Model call limits exceeded')
        cases = (
            ('text answer', [ai_message(content='Não sei.')], 8, True),
            ('refused output', [output_call, refused], 8, True),
            ('blocked output', [output_call, blocked], 8, False),
            ('data call', [data_call], 8, False),
            (
                'limit after refusal',
                [output_call, refused, output_call, refused, limit_message],
                2,
                True,
            ),
            (
                'limit after data',
                [data_call, data_call, limit_message],
                2,
                False,
            ),
            ('no model message', [HumanMessage(content='Oi')], 8, False),
        )
        for name, messages, max_calls, expected in cases:
            with self.subTest(case=name):
                self.assertIs(
                    is_invalid_output(messages, max_calls),
                    expected,
                )


# 10.12.6 and 10.12.7 -----------------------------------------------------


def create_agent_data(user):
    """Create 5 rows inside the current period, never in the future.

    Income 3000.00. Expense 1200.00 + 300.00 + 150.00 + 100.00 = 1750.00.
    Net 1250.00, savings rate 1250.00 / 3000.00 = 41.7%.
    """
    period_start, _ = calculate_analysis_period()
    account = create_account(user, 'Conta corrente', '100.00')
    salary = create_category(user, 'Salário', INCOME)
    expense = create_category(user, 'Despesas', EXPENSE)
    create_transaction(account, salary, '3000.00', period_start, 'Salário')
    for amount, description in (
        ('1200.00', 'Aluguel'),
        ('300.00', 'Supermercado'),
        ('150.00', 'Farmácia'),
        ('100.00', 'Cinema'),
    ):
        create_transaction(
            account, expense, amount, period_start, description,
        )


def summary_call():
    period_start, period_end = calculate_analysis_period()
    return ('get_financial_summary', {
        'start_date': period_start.isoformat(),
        'end_date': period_end.isoformat(),
    })


def tool_messages(messages, name=None):
    return [
        message
        for message in messages
        if message.type == 'tool' and (name is None or message.name == name)
    ]


@override_settings(**AI_SETTINGS)
class AgentTests(TransactionTestCase):
    """Full agent runs: the tools run in other threads (PRD 14.17)."""

    def setUp(self):
        self.user = create_user('agente@finanpy.test')
        create_agent_data(self.user)
        period_start, period_end = calculate_analysis_period()
        self.context = AnalysisContext(
            user_id=self.user.pk,
            period_start=period_start,
            period_end=period_end,
            deadline=time.monotonic() + 60,
            owner_thread_id=threading.get_ident(),
        )

    def run_with(self, model, context=None):
        tracker = RunTracker()
        with mock.patch('ai.agent.build_chat_model', return_value=model):
            run = run_agent(context or self.context, tracker=tracker)
        return run, tracker

    def test_tool_call_and_structured_output(self):
        model = fake_model(
            ai_message([summary_call(), ('get_accounts_overview', {})]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        run, tracker = self.run_with(model)

        self.assertIsInstance(run.structured_response, AnalysisOutput)
        self.assertEqual(
            run.structured_response.model_dump(mode='json'),
            build_output(),
        )
        summary = tool_messages(run.messages, 'get_financial_summary')[0]
        self.assertEqual(json.loads(summary.content), SUMMARY_DATA)
        overview = tool_messages(run.messages, 'get_accounts_overview')[0]
        # 100.00 + 3000.00 - 1750.00 = 1350.00
        self.assertEqual(
            json.loads(overview.content)['total_balance'],
            '1350.00',
        )
        self.assertEqual(
            (run.input_tokens, run.output_tokens, run.total_tokens),
            (200, 40, 240),
        )
        self.assertEqual(len(tracker.ai_messages), 2)
        self.assertTrue(validate_output(
            run.structured_response.model_dump(mode='json'),
            run.messages,
        ).is_verified)

    def test_retry_after_invalid_output(self):
        invalid = build_output()
        invalid['recommendations'] = []
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', invalid)]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        run, _ = self.run_with(model)

        refusals = tool_messages(run.messages, 'AnalysisOutput')
        self.assertTrue(refusals[0].content.startswith('Error:'))
        self.assertIsNotNone(run.structured_response)
        self.assertEqual(run.total_tokens, 360)

    def test_tool_error_is_returned_to_the_model(self):
        # Both the context error and the schema error become tool messages,
        # and the run goes on to the output.
        model = fake_model(
            ai_message([
                ('get_category_changes', {'month': '2000-01', 'limit': 5}),
                ('get_recurring_expenses', {'limit': 99}),
            ]),
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        run, _ = self.run_with(model)

        changes = tool_messages(run.messages, 'get_category_changes')[0]
        self.assertEqual(
            json.loads(changes.content)['error'],
            'month_out_of_period',
        )
        recurring = tool_messages(run.messages, 'get_recurring_expenses')[0]
        self.assertEqual(recurring.status, 'error')
        self.assertIsNotNone(run.structured_response)

    @override_settings(
        AI_MODEL_NAME='modelo-configurado',
        AI_MODEL_TIMEOUT_SECONDS=33,
        AI_MODEL_MAX_RETRIES=2,
        AI_MAX_OUTPUT_TOKENS=1234,
        AI_REASONING_EFFORT='low',
    )
    def test_chat_model_comes_from_the_settings(self):
        # Building the client makes no request. temperature is never sent.
        from ai.agent import build_chat_model

        model = build_chat_model()

        self.assertEqual(model.model_name, 'modelo-configurado')
        self.assertEqual(model.request_timeout, 33)
        self.assertEqual(model.max_retries, 2)
        self.assertEqual(model.max_tokens, 1234)
        self.assertEqual(model.reasoning_effort, 'low')
        self.assertIsNone(model.temperature)
        self.assertEqual(
            model.openai_api_key.get_secret_value(),
            'test-key-not-used',
        )

    def test_text_answer_ends_without_output(self):
        run, _ = self.run_with(fake_model(ai_message(content='Pronto.')))

        self.assertIsNone(run.structured_response)
        self.assertTrue(is_invalid_output(run.messages, 8))

    @override_settings(AI_MAX_MODEL_CALLS=2)
    def test_model_call_limit_ends_the_run(self):
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('get_accounts_overview', {})]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        run, tracker = self.run_with(model)

        self.assertIsNone(run.structured_response)
        self.assertEqual(len(tracker.ai_messages), 2)
        # The third message was never requested from the model.
        self.assertEqual(len(list(model.messages)), 1)
        self.assertFalse(is_invalid_output(run.messages, 2))

    @override_settings(AI_MAX_TOOL_CALLS=2)
    def test_tool_call_limit_blocks_the_extra_calls(self):
        model = fake_model(
            ai_message([
                summary_call(),
                ('get_accounts_overview', {}),
                ('get_recurring_expenses', {'limit': 5}),
            ]),
            ai_message([('AnalysisOutput', build_output())]),
            ai_message(content='Sem mais chamadas.'),
        )

        with mock.patch.object(
            queries,
            'get_recurring_expenses',
            wraps=queries.get_recurring_expenses,
        ) as recurring_query:
            run, _ = self.run_with(model)

        recurring = tool_messages(run.messages, 'get_recurring_expenses')[0]
        self.assertEqual(recurring.status, 'error')
        recurring_query.assert_not_called()
        self.assertEqual(
            len(tool_messages(run.messages, 'get_financial_summary')),
            1,
        )
        # The output past the limit is still delivered, and the run ends
        # there: the third message is never requested.
        self.assertIsNotNone(run.structured_response)
        self.assertEqual(len(list(model.messages)), 1)

    def test_deadline_ends_the_run_before_the_model(self):
        context = AnalysisContext(
            user_id=self.user.pk,
            period_start=self.context.period_start,
            period_end=self.context.period_end,
            deadline=time.monotonic() - 1,
            owner_thread_id=threading.get_ident(),
        )
        model = fake_model(ai_message([summary_call()]))

        run, tracker = self.run_with(model, context)

        self.assertIsNone(run.structured_response)
        self.assertEqual(tracker.ai_messages, [])
        self.assertEqual(len(list(model.messages)), 1)

    def test_deadline_is_checked_before_every_model_call(self):
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )
        clock = mock.Mock()
        # The first check is before the deadline, the next ones after it.
        clock.monotonic.side_effect = itertools.chain(
            [0.0],
            itertools.repeat(float('inf')),
        )
        context = AnalysisContext(
            user_id=self.user.pk,
            period_start=self.context.period_start,
            period_end=self.context.period_end,
            deadline=100.0,
            owner_thread_id=threading.get_ident(),
        )

        with mock.patch('ai.agent.time', clock):
            run, tracker = self.run_with(model, context)

        self.assertIsNone(run.structured_response)
        self.assertEqual(len(tracker.ai_messages), 1)
        self.assertEqual(
            len(tool_messages(run.messages, 'get_financial_summary')),
            1,
        )
        self.assertEqual(len(list(model.messages)), 1)


# 10.12.9 ---------------------------------------------------------------


def api_request():
    return httpx2.Request('POST', 'https://api.openai.com/v1/responses')


def api_status_error(error_class, status_code):
    return error_class(
        'mensagem do provedor',
        response=httpx2.Response(status_code, request=api_request()),
        body=None,
    )


@override_settings(**AI_SETTINGS)
class GenerateAnalysisTests(TransactionTestCase):
    def setUp(self):
        self.user = create_user('servico@finanpy.test')

    def generate_with(self, model):
        with mock.patch('ai.agent.build_chat_model', return_value=model):
            return generate_analysis(self.user)

    def latest(self):
        return FinancialAnalysis.objects.filter(user=self.user).latest('pk')

    @override_settings(OPENAI_API_KEY='')
    def test_disabled_without_key(self):
        create_agent_data(self.user)

        with mock.patch('ai.agent.build_chat_model') as build:
            outcome = generate_analysis(self.user)

        self.assertEqual(outcome, GenerationOutcome.DISABLED)
        build.assert_not_called()
        self.assertFalse(FinancialAnalysis.objects.exists())

    def test_insufficient_data(self):
        # 4 rows, below the minimum of 5. Future rows do not count.
        account = create_account(self.user, 'Conta')
        category = create_category(self.user, 'Mercado', EXPENSE)
        today = timezone.localdate()
        for _ in range(4):
            create_transaction(account, category, '10.00', today, 'Feira')
        create_transaction(
            account, category, '10.00', today + timedelta(days=1), 'Feira',
        )

        with mock.patch('ai.agent.build_chat_model') as build:
            outcome = generate_analysis(self.user)

        self.assertEqual(outcome, GenerationOutcome.INSUFFICIENT_DATA)
        build.assert_not_called()
        self.assertFalse(FinancialAnalysis.objects.exists())

    def create_analysis(self, **fields):
        period_start, period_end = calculate_analysis_period()
        return FinancialAnalysis.objects.create(
            user=self.user,
            period_start=period_start,
            period_end=period_end,
            model_name='fake',
            prompt_version='1',
            **fields,
        )

    def test_limit_reached_counts_failures(self):
        create_agent_data(self.user)
        for status in (Status.SUCCESS, Status.FAILED, Status.FAILED):
            self.create_analysis(status=status)

        with mock.patch('ai.agent.build_chat_model') as build:
            outcome = generate_analysis(self.user)

        self.assertEqual(outcome, GenerationOutcome.LIMIT_REACHED)
        build.assert_not_called()

    def test_limit_ignores_yesterday(self):
        create_agent_data(self.user)
        for _ in range(3):
            analysis = self.create_analysis(status=Status.FAILED)
        FinancialAnalysis.objects.update(
            created_at=timezone.now() - timedelta(days=1),
        )
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        self.assertEqual(self.generate_with(model), GenerationOutcome.SUCCESS)
        self.assertNotEqual(self.latest().pk, analysis.pk)

    def test_already_running(self):
        create_agent_data(self.user)
        self.create_analysis()

        with mock.patch('ai.agent.build_chat_model') as build:
            outcome = generate_analysis(self.user)

        self.assertEqual(outcome, GenerationOutcome.ALREADY_RUNNING)
        build.assert_not_called()
        self.assertEqual(FinancialAnalysis.objects.count(), 1)

    def test_abandoned_pending_is_closed_before_a_new_run(self):
        create_agent_data(self.user)
        old = self.create_analysis()
        FinancialAnalysis.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(minutes=6),
        )
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        outcome = self.generate_with(model)

        self.assertEqual(outcome, GenerationOutcome.SUCCESS)
        old.refresh_from_db()
        self.assertEqual(old.status, Status.FAILED)
        self.assertEqual(old.error_code, ErrorCode.ABANDONED)
        self.assertIsNotNone(old.finished_at)

    def test_success_records_the_run(self):
        create_agent_data(self.user)
        output = build_output(insight_values=('1250.00', '8888.88'))
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', output)]),
        )

        outcome = self.generate_with(model)

        self.assertEqual(outcome, GenerationOutcome.SUCCESS)
        analysis = self.latest()
        period_start, period_end = calculate_analysis_period()
        self.assertEqual(analysis.status, Status.SUCCESS)
        self.assertEqual(analysis.error_code, '')
        self.assertEqual(analysis.period_start, period_start)
        self.assertEqual(analysis.period_end, period_end)
        self.assertIsNotNone(analysis.generated_at)
        self.assertIsNotNone(analysis.finished_at)
        self.assertIsNotNone(analysis.duration_ms)
        self.assertEqual(analysis.main_insight, output['main_insight'])
        self.assertEqual(analysis.insights, [output['insights'][0]])
        self.assertEqual(analysis.recommendations, output['recommendations'])
        self.assertEqual(analysis.alerts, output['alerts'])
        self.assertEqual(analysis.data_limitations, [
            'O mês atual é parcial.',
            DISCARDED_ITEM_NOTES['insights'],
        ])
        self.assertEqual(analysis.metrics_snapshot, {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            **SUMMARY_DATA,
        })
        self.assertEqual(analysis.tool_calls, [{
            'name': summary_call()[0],
            'args': summary_call()[1],
        }])
        self.assertEqual(
            (
                analysis.input_tokens,
                analysis.output_tokens,
                analysis.total_tokens,
            ),
            (200, 40, 240),
        )

    def assert_failure(self, outcome, error_code, tokens=None):
        self.assertEqual(outcome, GenerationOutcome.FAILED)
        analysis = self.latest()
        self.assertEqual(analysis.status, Status.FAILED)
        self.assertEqual(analysis.error_code, error_code)
        self.assertIsNone(analysis.generated_at)
        self.assertIsNotNone(analysis.finished_at)
        self.assertIsNotNone(analysis.duration_ms)
        self.assertEqual(analysis.main_insight, {})
        if tokens is not None:
            self.assertEqual(analysis.total_tokens, tokens)
        return analysis

    def test_unverified_output(self):
        create_agent_data(self.user)
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output('9999.99'))]),
        )

        self.assert_failure(
            self.generate_with(model),
            ErrorCode.UNVERIFIED_OUTPUT,
            tokens=240,
        )

    def test_invalid_output_after_a_text_answer(self):
        create_agent_data(self.user)
        model = fake_model(ai_message(content='Não consigo.'))

        self.assert_failure(
            self.generate_with(model),
            ErrorCode.INVALID_OUTPUT,
            tokens=120,
        )

    @override_settings(AI_MAX_MODEL_CALLS=2)
    def test_invalid_output_when_the_limit_follows_a_refusal(self):
        create_agent_data(self.user)
        invalid = build_output()
        invalid['recommendations'] = []
        model = fake_model(
            ai_message([('AnalysisOutput', invalid)]),
            ai_message([('AnalysisOutput', invalid)]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        self.assert_failure(
            self.generate_with(model),
            ErrorCode.INVALID_OUTPUT,
        )

    @override_settings(AI_MAX_MODEL_CALLS=2)
    def test_limit_exceeded_without_output(self):
        create_agent_data(self.user)
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('get_accounts_overview', {})]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        analysis = self.assert_failure(
            self.generate_with(model),
            ErrorCode.LIMIT_EXCEEDED,
            tokens=240,
        )
        self.assertEqual(
            [call['name'] for call in analysis.tool_calls],
            ['get_financial_summary', 'get_accounts_overview'],
        )

    @override_settings(AI_RUN_BUDGET_SECONDS=0)
    def test_timeout_by_the_run_deadline(self):
        create_agent_data(self.user)
        model = fake_model(ai_message([summary_call()]))

        self.assert_failure(
            self.generate_with(model),
            ErrorCode.TIMEOUT,
            tokens=0,
        )

    def test_exceptions_map_to_error_codes(self):
        create_agent_data(self.user)
        cases = (
            (
                api_status_error(openai.AuthenticationError, 401),
                ErrorCode.AUTHENTICATION_ERROR,
            ),
            (
                api_status_error(openai.PermissionDeniedError, 403),
                ErrorCode.AUTHENTICATION_ERROR,
            ),
            (
                api_status_error(openai.NotFoundError, 404),
                ErrorCode.MODEL_UNAVAILABLE,
            ),
            (
                api_status_error(openai.RateLimitError, 429),
                ErrorCode.RATE_LIMITED,
            ),
            (
                openai.APITimeoutError(request=api_request()),
                ErrorCode.TIMEOUT,
            ),
            (
                openai.APIConnectionError(request=api_request()),
                ErrorCode.PROVIDER_UNAVAILABLE,
            ),
            (
                api_status_error(openai.InternalServerError, 500),
                ErrorCode.PROVIDER_UNAVAILABLE,
            ),
            (
                GraphRecursionError('Recursion limit reached.'),
                ErrorCode.LIMIT_EXCEEDED,
            ),
            (
                StructuredOutputValidationError(
                    'AnalysisOutput',
                    ValueError('saída'),
                    AIMessage(content=''),
                ),
                ErrorCode.INVALID_OUTPUT,
            ),
            (
                MultipleStructuredOutputsError(
                    ['AnalysisOutput', 'AnalysisOutput'],
                    AIMessage(content=''),
                ),
                ErrorCode.INVALID_OUTPUT,
            ),
            (ValueError('qualquer outra'), ErrorCode.INTERNAL_ERROR),
        )
        for error, error_code in cases:
            with self.subTest(error=type(error).__name__):
                FinancialAnalysis.objects.all().delete()
                with mock.patch.object(
                    ToolCallingFakeChatModel,
                    '_generate',
                    side_effect=error,
                ), self.assertLogs('ai.services', 'ERROR') as logs:
                    outcome = self.generate_with(fake_model())
                analysis = self.assert_failure(outcome, error_code)
                self.assertEqual(analysis.error_detail, type(error).__name__)
                # Only the class of the exception is logged, never its text.
                self.assertNotIn(
                    'mensagem do provedor',
                    '\n'.join(logs.output),
                )

    def test_database_error_in_a_tool_is_an_internal_error(self):
        create_agent_data(self.user)
        model = fake_model(
            ai_message([('get_accounts_overview', {})]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        with mock.patch.object(
            queries,
            'get_accounts_overview',
            side_effect=DatabaseError('dados sensíveis'),
        ), self.assertLogs('ai.services', 'ERROR') as logs:
            outcome = self.generate_with(model)

        analysis = self.assert_failure(outcome, ErrorCode.INTERNAL_ERROR)
        self.assertEqual(analysis.error_detail, 'DatabaseError')
        self.assertNotIn('dados sensíveis', '\n'.join(logs.output))
        # The call that ran before the error keeps its tokens.
        self.assertEqual(analysis.total_tokens, 120)

    def test_run_inside_a_transaction_is_refused(self):
        create_agent_data(self.user)
        model = fake_model(ai_message([summary_call()]))

        connection = mock.Mock(in_atomic_block=True)
        with mock.patch('ai.services.connection', connection), \
                self.assertLogs('ai.services', 'ERROR'):
            outcome = self.generate_with(model)

        self.assert_failure(outcome, ErrorCode.INTERNAL_ERROR, tokens=0)
        self.assertEqual(len(list(model.messages)), 1)

    def test_failed_final_write_leaves_the_record_pending(self):
        create_agent_data(self.user)
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        with mock.patch(
            'ai.services._finish_analysis',
            side_effect=DatabaseError('falha'),
        ), self.assertLogs('ai.services', 'ERROR'):
            outcome = self.generate_with(model)

        self.assertEqual(outcome, GenerationOutcome.FAILED)
        self.assertEqual(self.latest().status, Status.PENDING)

    def test_closed_record_is_not_overwritten(self):
        # A record closed as abandoned during the run stays as it is (RN07).
        create_agent_data(self.user)
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        def close_record(*args, **kwargs):
            FinancialAnalysis.objects.update(
                status=Status.FAILED,
                error_code=ErrorCode.ABANDONED,
            )
            return original_run_agent(*args, **kwargs)

        from ai import agent
        original_run_agent = agent.run_agent
        with mock.patch('ai.agent.run_agent', side_effect=close_record):
            outcome = self.generate_with(model)

        self.assertEqual(outcome, GenerationOutcome.FAILED)
        analysis = self.latest()
        self.assertEqual(analysis.error_code, ErrorCode.ABANDONED)
        self.assertEqual(analysis.main_insight, {})

    def test_unexpected_error_before_the_run_never_propagates(self):
        with mock.patch(
            'ai.services._close_abandoned_analyses',
            side_effect=DatabaseError('falha'),
        ), self.assertLogs('ai.services', 'ERROR'):
            outcome = generate_analysis(self.user)

        self.assertEqual(outcome, GenerationOutcome.FAILED)


# 10.12.10 --------------------------------------------------------------

# Texts of PRD 14.15, written by hand and never imported from ai.views.
OUTCOME_MESSAGE_TEXTS = {
    GenerationOutcome.SUCCESS: (
        message_constants.SUCCESS,
        'Análise gerada com sucesso.',
    ),
    GenerationOutcome.FAILED: (
        message_constants.ERROR,
        'Não foi possível gerar a análise. Tente novamente mais tarde.',
    ),
    GenerationOutcome.ALREADY_RUNNING: (
        message_constants.ERROR,
        'Já existe uma análise em andamento.',
    ),
    GenerationOutcome.LIMIT_REACHED: (
        message_constants.ERROR,
        'Você atingiu o limite de análises de hoje.',
    ),
    GenerationOutcome.INSUFFICIENT_DATA: (
        message_constants.ERROR,
        'Ainda não há transações suficientes para gerar uma análise.',
    ),
    GenerationOutcome.DISABLED: (
        message_constants.ERROR,
        'O assistente não está disponível no momento.',
    ),
}

LIST_EMPTY_TEXT = (
    'Você ainda não tem análises. Gere a primeira no dashboard para receber '
    'dicas sobre suas finanças.'
)
DISCLAIMER_TEXT = (
    'Conteúdo gerado por inteligência artificial, com caráter educativo, a '
    'partir dos seus lançamentos.'
)


def create_analysis_record(user, status=Status.SUCCESS, title='', **fields):
    """Create an analysis directly, as the service would leave it."""
    period_start, period_end = calculate_analysis_period()
    if status == Status.SUCCESS:
        fields.setdefault('generated_at', timezone.now())
    if title:
        fields.setdefault('main_insight', {
            'title': title,
            'description': 'Descrição do insight.',
            'evidence': [evidence('3000.00')],
        })
    return FinancialAnalysis.objects.create(
        user=user,
        status=status,
        period_start=period_start,
        period_end=period_end,
        model_name='fake',
        prompt_version='1',
        **fields,
    )


def login_redirect(url):
    return f'{reverse("login")}?next={url}'


class ModelNotCalledMixin:
    """Fail the test if anything reaches the agent or the service."""

    def setUp(self):
        super().setUp()
        self.mocks = {}
        for target in (
            'ai.agent.build_chat_model',
            'ai.agent.run_agent',
            'ai.views.generate_analysis',
        ):
            patcher = mock.patch(target)
            self.mocks[target] = patcher.start()
            self.addCleanup(patcher.stop)

    def assert_model_not_called(self):
        for target, mocked in self.mocks.items():
            with self.subTest(target=target):
                mocked.assert_not_called()


@override_settings(**AI_SETTINGS)
class AnalysisLoginRequiredTests(ModelNotCalledMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('login@finanpy.test')
        cls.analysis = create_analysis_record(cls.user, title='Insight')

    def test_list_redirects_to_login(self):
        url = reverse('ai:list')

        response = self.client.get(url)

        self.assertRedirects(response, login_redirect(url))

    def test_detail_redirects_to_login(self):
        url = reverse('ai:detail', args=[self.analysis.pk])

        response = self.client.get(url)

        self.assertRedirects(response, login_redirect(url))

    def test_create_redirects_to_login_without_generating(self):
        url = reverse('ai:create')

        response = self.client.post(url)

        self.assertRedirects(response, login_redirect(url))
        self.assert_model_not_called()
        self.assertEqual(FinancialAnalysis.objects.count(), 1)

    def test_create_get_redirects_anonymous_user_to_login(self):
        url = reverse('ai:create')

        response = self.client.get(url)

        self.assertRedirects(response, login_redirect(url))


@override_settings(**AI_SETTINGS)
class AnalysisCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('gerar@finanpy.test')
        cls.url = reverse('ai:create')

    def setUp(self):
        self.client.force_login(self.user)

    def post_with(self, outcome, **kwargs):
        with mock.patch(
            'ai.views.generate_analysis',
            return_value=outcome,
        ) as generate:
            response = self.client.post(self.url, **kwargs)
        return response, generate

    def test_post_calls_service_with_request_user_and_redirects(self):
        response, generate = self.post_with(GenerationOutcome.SUCCESS)

        generate.assert_called_once()
        (user,), kwargs = generate.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(user.pk, self.user.pk)
        self.assertRedirects(
            response,
            reverse('dashboard'),
            fetch_redirect_response=False,
        )

    def test_get_returns_405_without_generating(self):
        with mock.patch('ai.views.generate_analysis') as generate:
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'POST')
        generate.assert_not_called()

    def test_other_methods_return_405(self):
        with mock.patch('ai.views.generate_analysis') as generate:
            for method in ('put', 'patch', 'delete'):
                with self.subTest(method=method):
                    response = getattr(self.client, method)(self.url)
                    self.assertEqual(response.status_code, 405)
        generate.assert_not_called()

    def test_post_without_csrf_token_is_refused(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        with mock.patch('ai.views.generate_analysis') as generate:
            response = client.post(self.url)

        self.assertEqual(response.status_code, 403)
        generate.assert_not_called()

    def test_each_outcome_shows_the_message_of_the_prd(self):
        # Every member of the enum must have a message, none left over.
        self.assertEqual(
            set(OUTCOME_MESSAGE_TEXTS),
            set(GenerationOutcome),
        )
        for outcome, (level, text) in OUTCOME_MESSAGE_TEXTS.items():
            with self.subTest(outcome=outcome):
                # A new session, so the messages of the previous outcome,
                # never displayed, do not pile up.
                self.client = Client()
                self.client.force_login(self.user)
                response, _ = self.post_with(outcome)

                stored = list(get_messages(response.wsgi_request))
                self.assertEqual(len(stored), 1)
                self.assertEqual(stored[0].level, level)
                self.assertEqual(stored[0].message, text)
                self.assertRedirects(
                    response,
                    reverse('dashboard'),
                    fetch_redirect_response=False,
                )

    def test_message_appears_on_the_dashboard(self):
        response, _ = self.post_with(
            GenerationOutcome.LIMIT_REACHED,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(
            response,
            'Você atingiu o limite de análises de hoje.',
        )


@override_settings(**AI_SETTINGS)
class AnalysisCreateViewIntegrationTests(TransactionTestCase):
    """The view with the real service: the agent runs only with a fake."""

    def setUp(self):
        self.user = create_user('integracao@finanpy.test')
        self.client.force_login(self.user)
        self.url = reverse('ai:create')

    def stored_messages(self, response):
        return [
            (message.level, message.message)
            for message in get_messages(response.wsgi_request)
        ]

    def test_successful_run_with_fake_model(self):
        create_agent_data(self.user)
        model = fake_model(
            ai_message([summary_call()]),
            ai_message([('AnalysisOutput', build_output())]),
        )

        with mock.patch('ai.agent.build_chat_model', return_value=model):
            response = self.client.post(self.url)

        self.assertRedirects(
            response,
            reverse('dashboard'),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            self.stored_messages(response),
            [(message_constants.SUCCESS, 'Análise gerada com sucesso.')],
        )
        analysis = FinancialAnalysis.objects.get(user=self.user)
        self.assertEqual(analysis.status, Status.SUCCESS)

    @override_settings(OPENAI_API_KEY='')
    def test_without_key_the_model_is_never_built(self):
        create_agent_data(self.user)

        with mock.patch('ai.agent.build_chat_model') as build:
            response = self.client.post(self.url)

        build.assert_not_called()
        self.assertEqual(
            self.stored_messages(response),
            [(
                message_constants.ERROR,
                'O assistente não está disponível no momento.',
            )],
        )
        self.assertFalse(FinancialAnalysis.objects.exists())

    def test_insufficient_data_never_builds_the_model(self):
        with mock.patch('ai.agent.build_chat_model') as build:
            response = self.client.post(self.url)

        build.assert_not_called()
        self.assertEqual(
            self.stored_messages(response),
            [(
                message_constants.ERROR,
                'Ainda não há transações suficientes para gerar uma análise.',
            )],
        )


@override_settings(**AI_SETTINGS)
class AnalysisListViewTests(ModelNotCalledMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('lista@finanpy.test')
        cls.other = create_user('lista.outro@finanpy.test')
        cls.url = reverse('ai:list')

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def create_history(self, user, count, prefix):
        """Create count analyses, one hour apart, the last one the newest."""
        start = timezone.now() - timedelta(hours=count)
        created = []
        for index in range(count):
            analysis = create_analysis_record(
                user,
                status=Status.FAILED if index % 2 else Status.SUCCESS,
                title=f'{prefix} {index:02d}',
            )
            FinancialAnalysis.objects.filter(pk=analysis.pk).update(
                created_at=start + timedelta(hours=index),
            )
            created.append(analysis)
        return created

    def test_empty_state(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai/analysis_list.html')
        self.assertEqual(list(response.context['analyses']), [])
        self.assertContains(response, LIST_EMPTY_TEXT)
        self.assertContains(response, 'Ir para o dashboard')
        self.assert_model_not_called()

    def test_first_page_has_twenty_newest_first(self):
        created = self.create_history(self.user, 21, 'Minha')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        page = list(response.context['analyses'])
        self.assertEqual(len(page), 20)
        # Newest first: index 20 down to index 1.
        self.assertEqual(
            [analysis.pk for analysis in page],
            [analysis.pk for analysis in reversed(created[1:])],
        )
        self.assertTrue(response.context['is_paginated'])
        self.assertContains(response, 'Página 1 de 2')
        self.assertNotContains(response, LIST_EMPTY_TEXT)
        self.assertContains(response, DISCLAIMER_TEXT)
        self.assert_model_not_called()

    def test_second_page_has_the_oldest(self):
        created = self.create_history(self.user, 21, 'Minha')

        response = self.client.get(self.url, {'page': 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['analyses']), [created[0]])
        self.assertContains(response, 'Página 2 de 2')

    def test_page_out_of_range_is_404(self):
        self.create_history(self.user, 3, 'Minha')

        response = self.client.get(self.url, {'page': 2})

        self.assertEqual(response.status_code, 404)

    def test_same_created_at_keeps_a_stable_order(self):
        first = create_analysis_record(self.user, title='Primeira')
        second = create_analysis_record(self.user, title='Segunda')
        moment = timezone.now()
        FinancialAnalysis.objects.filter(user=self.user).update(
            created_at=moment,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            list(response.context['analyses']),
            [second, first],
        )

    def test_lists_only_the_own_analyses(self):
        self.create_history(self.other, 2, 'Do outro')
        mine = create_analysis_record(self.user, title='Minha análise')

        response = self.client.get(self.url)

        self.assertEqual(list(response.context['analyses']), [mine])
        self.assertContains(response, 'Minha análise')
        self.assertNotContains(response, 'Do outro')

    def test_shows_date_period_status_and_title(self):
        analysis = create_analysis_record(self.user, title='Gasto alto')
        create_analysis_record(self.user, status=Status.FAILED)
        period_start, period_end = calculate_analysis_period()

        response = self.client.get(self.url)

        self.assertContains(response, 'Gasto alto')
        self.assertContains(
            response,
            f'{period_start:%d/%m/%Y} a {period_end:%d/%m/%Y}',
        )
        self.assertContains(response, 'Concluída')
        self.assertContains(response, 'Falhou')
        self.assertContains(
            response,
            reverse('ai:detail', args=[analysis.pk]),
        )


@override_settings(**AI_SETTINGS)
class AnalysisDetailViewTests(ModelNotCalledMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('detalhe@finanpy.test')
        cls.other = create_user('detalhe.outro@finanpy.test')
        cls.analysis = create_analysis_record(
            cls.user,
            title='Insight da dona',
            recommendations=[item('1750.00')],
        )
        cls.other_analysis = create_analysis_record(
            cls.other,
            title='Insight do outro',
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def get_detail(self, analysis_pk):
        return self.client.get(reverse('ai:detail', args=[analysis_pk]))

    def test_own_analysis_returns_200(self):
        response = self.get_detail(self.analysis.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai/analysis_detail.html')
        self.assertEqual(response.context['analysis'], self.analysis)
        self.assertIsNone(response.context['stale_notice'])
        self.assertContains(response, 'Insight da dona')
        self.assertContains(response, DISCLAIMER_TEXT)
        self.assert_model_not_called()

    def test_analysis_of_another_user_returns_404(self):
        response = self.get_detail(self.other_analysis.pk)

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(
            response,
            'Insight do outro',
            status_code=404,
        )

    def test_missing_analysis_returns_404(self):
        response = self.get_detail(self.other_analysis.pk + 1000)

        self.assertEqual(response.status_code, 404)

    @override_settings(AI_ANALYSIS_STALE_DAYS=30)
    def test_stale_analysis_shows_the_notice(self):
        FinancialAnalysis.objects.filter(pk=self.analysis.pk).update(
            generated_at=timezone.now() - timedelta(days=31),
        )

        response = self.get_detail(self.analysis.pk)

        notice = (
            'Esta análise tem mais de 30 dias. Gere uma nova para refletir '
            'seus dados atuais.'
        )
        self.assertEqual(response.context['stale_notice'], notice)
        self.assertContains(response, notice)

    def test_failed_and_pending_analyses_render(self):
        for status, text in (
            (Status.FAILED, 'Não foi possível concluir esta análise.'),
            (Status.PENDING, 'Esta análise ainda está em andamento.'),
        ):
            with self.subTest(status=status):
                analysis = create_analysis_record(self.user, status=status)

                response = self.get_detail(analysis.pk)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)
                self.assertIsNone(response.context['stale_notice'])
                # Leave room for the pending record of the next subtest.
                analysis.delete()
        self.assert_model_not_called()


@override_settings(**AI_SETTINGS)
class AnalysisReadQueryTests(TestCase):
    """get_latest_valid_analysis and the dashboard state, PRD 14.14."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('consultas@finanpy.test')
        cls.other = create_user('consultas.outro@finanpy.test')
        create_agent_data(cls.user)

    def set_generated_at(self, analysis, days_ago):
        moment = timezone.now() - timedelta(days=days_ago)
        FinancialAnalysis.objects.filter(pk=analysis.pk).update(
            generated_at=moment,
            created_at=moment,
        )

    def test_latest_valid_is_the_last_success_by_generated_at(self):
        older = create_analysis_record(self.user, title='Antiga')
        newer = create_analysis_record(self.user, title='Nova')
        self.set_generated_at(older, 2)
        self.set_generated_at(newer, 1)
        # Failures and pending runs are never the valid analysis, and the
        # last one created is not necessarily the newest by generated_at.
        create_analysis_record(self.user, status=Status.FAILED)
        create_analysis_record(self.user, status=Status.PENDING)
        create_analysis_record(self.other, title='Do outro')

        with self.assertNumQueries(1):
            latest = get_latest_valid_analysis(self.user)

        self.assertEqual(latest, newer)

    def test_latest_valid_is_none_without_success(self):
        create_analysis_record(self.user, status=Status.FAILED)
        create_analysis_record(self.other, title='Do outro')

        with self.assertNumQueries(1):
            self.assertIsNone(get_latest_valid_analysis(self.user))

    def test_dashboard_state_uses_at_most_three_queries(self):
        # The longest path: key, data and a valid analysis.
        create_analysis_record(self.user, title='Insight')

        with self.assertNumQueries(3):
            state = get_dashboard_analysis_state(self.user)

        self.assertEqual(state['state'], AnalysisState.WITH_ANALYSIS)

    def test_query_count_does_not_grow_with_history(self):
        for days_ago in range(1, 30):
            analysis = create_analysis_record(self.user, title='Antiga')
            self.set_generated_at(analysis, days_ago)
        create_analysis_record(self.user, status=Status.FAILED)

        with self.assertNumQueries(3):
            get_dashboard_analysis_state(self.user)

    def test_every_state_stays_within_three_queries(self):
        scenarios = {
            'disabled': {'OPENAI_API_KEY': ''},
            'insufficient': {'AI_ANALYSIS_MIN_TRANSACTIONS': 50},
            'limit': {'AI_ANALYSIS_DAILY_LIMIT': 0},
            'default': {},
        }
        for name, overrides in scenarios.items():
            with self.subTest(scenario=name), self.settings(**overrides):
                with CaptureQueriesContext(connection) as queries_run:
                    get_dashboard_analysis_state(self.user)
                self.assertLessEqual(len(queries_run), 3)

        create_analysis_record(self.user, status=Status.PENDING)
        with CaptureQueriesContext(connection) as queries_run:
            state = get_dashboard_analysis_state(self.user)
        self.assertEqual(state['state'], AnalysisState.RUNNING)
        self.assertLessEqual(len(queries_run), 3)

    def test_dashboard_state_never_writes(self):
        pending = create_analysis_record(self.user, status=Status.PENDING)
        FinancialAnalysis.objects.filter(pk=pending.pk).update(
            created_at=timezone.now() - timedelta(minutes=10),
        )

        with CaptureQueriesContext(connection) as queries_run:
            state = get_dashboard_analysis_state(self.user)

        self.assertTrue(all(
            query['sql'].lstrip().upper().startswith('SELECT')
            for query in queries_run
        ))
        pending.refresh_from_db()
        # An old pending run is neither running nor closed by a read.
        self.assertEqual(pending.status, Status.PENDING)
        self.assertNotEqual(state['state'], AnalysisState.RUNNING)


LANGCHAIN_IMPORT_SCRIPT = """
import json
import sys

import django

django.setup()

from django.core.management import call_command
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse
from django.utils import timezone

setup_test_environment()
call_command('migrate', verbosity=0)

from ai.models import FinancialAnalysis
from users.models import User

user = User.objects.create_user(email='import@finanpy.test', password='x')
today = timezone.localdate()
analysis = FinancialAnalysis.objects.create(
    user=user,
    status='success',
    period_start=today,
    period_end=today,
    generated_at=timezone.now(),
    main_insight={'title': 'Insight', 'description': 'Texto', 'evidence': []},
    model_name='fake',
    prompt_version='1',
)
client = Client()
client.force_login(user)
codes = [
    client.get(reverse('dashboard')).status_code,
    client.get(reverse('ai:list')).status_code,
    client.get(reverse('ai:detail', args=[analysis.pk])).status_code,
]
prefixes = ('langchain', 'langgraph', 'langsmith', 'openai')
loaded = sorted(
    name for name in sys.modules if name.split('.')[0].startswith(prefixes)
)
print(json.dumps({'codes': codes, 'loaded': loaded}))
"""


class LangChainNotImportedTests(SimpleTestCase):
    """RNF23: the pages load without importing LangChain or OpenAI.

    The test process has already imported LangChain, so the check runs in
    a new interpreter, with its own database in memory.
    """

    def test_pages_do_not_import_langchain(self):
        env = {
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'core.settings',
            'DATABASE_PATH': ':memory:',
            'OPENAI_API_KEY': 'test-key-not-used',
        }
        result = subprocess.run(
            [sys.executable, '-c', LANGCHAIN_IMPORT_SCRIPT],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(report['codes'], [200, 200, 200])
        self.assertEqual(report['loaded'], [])


# 10.12.11 --------------------------------------------------------------


@skipUnless(
    os.environ.get('RUN_LIVE_AI_TESTS') == 'True',
    'Teste real com a OpenAI: defina RUN_LIVE_AI_TESTS=True (gera custo).',
)
class LiveAnalysisTests(TransactionTestCase):
    """Run one analysis against the real API and measure time and cost.

    Needs OPENAI_API_KEY in the environment and the authorization of the
    person responsible, since it is charged. Prints only numbers.
    """

    def test_real_analysis(self):
        if not settings.OPENAI_API_KEY:
            self.skipTest('OPENAI_API_KEY não definida.')
        user = create_user('teste-real@finanpy.test')
        create_agent_data(user)

        started_at = time.perf_counter()
        outcome = generate_analysis(user)
        elapsed = time.perf_counter() - started_at

        analysis = FinancialAnalysis.objects.get(user=user)
        cost = (
            analysis.input_tokens * LIVE_INPUT_PRICE_PER_MILLION
            + analysis.output_tokens * LIVE_OUTPUT_PRICE_PER_MILLION
        ) / Decimal('1000000')
        print(
            f'\n[live] model={analysis.model_name} outcome={outcome} '
            f'error_code={analysis.error_code or "-"} '
            f'elapsed_s={elapsed:.1f} duration_ms={analysis.duration_ms} '
            f'input_tokens={analysis.input_tokens} '
            f'output_tokens={analysis.output_tokens} '
            f'total_tokens={analysis.total_tokens} '
            f'tool_calls={len(analysis.tool_calls)} '
            f'estimated_cost_usd={cost:.5f} '
            f'(no cached input discount)'
        )
        self.assertEqual(outcome, GenerationOutcome.SUCCESS)
        self.assertGreater(analysis.total_tokens, 0)
        self.assertLess(elapsed, settings.AI_RUN_BUDGET_SECONDS + 90)
