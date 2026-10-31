from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction

User = get_user_model()

# A view lê o mês corrente de timezone.localdate. Os testes congelam essa data
# para que o resultado não dependa do dia em que a suíte é executada.
TODAY = date(2026, 3, 15)


def create_account(user, name='Conta corrente', initial_balance='0.00'):
    return Account.objects.create(
        user=user,
        name=name,
        account_type=Account.AccountType.CHECKING,
        initial_balance=Decimal(initial_balance),
    )


def create_category(user, category_type, name):
    return Category.objects.create(
        user=user,
        name=name,
        category_type=category_type,
    )


def create_transaction(
    account, category, amount, on_date, description='Lançamento de teste'
):
    return Transaction.objects.create(
        user=account.user,
        transaction_type=category.category_type,
        amount=Decimal(amount),
        date=on_date,
        description=description,
        account=account,
        category=category,
    )


class DashboardTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email='dono@finanpy.test',
            password='SenhaForte!123',
            first_name='Dona',
        )
        cls.other_user = User.objects.create_user(
            email='outro@finanpy.test',
            password='SenhaForte!123',
            first_name='Outro',
        )
        cls.income_category = create_category(
            cls.owner, Category.CategoryType.INCOME, 'Salário'
        )
        cls.expense_category = create_category(
            cls.owner, Category.CategoryType.EXPENSE, 'Mercado'
        )
        cls.dashboard_url = reverse('dashboard')

    def setUp(self):
        self.client.force_login(self.owner)

    def get_dashboard(self, today=TODAY):
        with patch('core.views.timezone.localdate', return_value=today):
            return self.client.get(self.dashboard_url)


class LandingPageTests(TestCase):
    def test_landing_is_public_for_anonymous_user(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_landing_invites_anonymous_user_to_sign_up_and_log_in(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Cadastre-se')
        self.assertContains(response, 'Entrar')
        self.assertNotContains(response, 'Ir para o dashboard')

    def test_landing_links_authenticated_user_to_dashboard(self):
        user = User.objects.create_user(
            email='dono@finanpy.test',
            password='SenhaForte!123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ir para o dashboard')


class DashboardAccessTests(TestCase):
    def test_anonymous_user_is_redirected_to_login_with_next(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, '/login/?next=/dashboard/')

    def test_authenticated_user_can_open_dashboard(self):
        user = User.objects.create_user(
            email='dono@finanpy.test',
            password='SenhaForte!123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')


class DashboardKpiTests(DashboardTestCase):
    """Cenário com duas contas e lançamentos dentro e fora de março de 2026.

    Março/2026: entradas 3000,00 + 234,56 = 3234,56;
    saídas 1500,25 + 34,56 = 1534,81; resultado 1699,75.
    Banco Alfa: 1000,00 + 3000,00 - 1500,25 + 500,00 - 120,00 = 2879,75.
    Carteira: 200,50 + 234,56 - 34,56 - 80,00 = 320,50.
    Saldo total: 2879,75 + 320,50 = 3200,25.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bank = create_account(cls.owner, 'Banco Alfa', '1000.00')
        cls.wallet = create_account(cls.owner, 'Carteira', '200.50')
        create_transaction(
            cls.bank, cls.income_category, '3000.00', date(2026, 3, 5)
        )
        create_transaction(
            cls.wallet, cls.income_category, '234.56', date(2026, 3, 10)
        )
        create_transaction(
            cls.bank, cls.expense_category, '1500.25', date(2026, 3, 12)
        )
        create_transaction(
            cls.wallet, cls.expense_category, '34.56', date(2026, 3, 14)
        )
        # Fora do mês: último dia do mês anterior, primeiro dia do mês
        # seguinte e o mesmo mês do ano anterior.
        create_transaction(
            cls.bank, cls.income_category, '500.00', date(2026, 2, 28)
        )
        create_transaction(
            cls.bank, cls.expense_category, '120.00', date(2026, 4, 1)
        )
        create_transaction(
            cls.wallet, cls.expense_category, '80.00', date(2025, 3, 15)
        )

    def test_total_balance_includes_every_account_and_month(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['total_balance'], Decimal('3200.25'))

    def test_month_income_ignores_other_months(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['month_income'], Decimal('3234.56'))

    def test_month_expense_ignores_other_months(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['month_expense'], Decimal('1534.81'))

    def test_positive_month_result(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['month_result'], Decimal('1699.75'))
        self.assertEqual(
            response.context['month_result_abs'], Decimal('1699.75')
        )

    def test_account_list_shows_each_current_balance(self):
        response = self.get_dashboard()

        accounts = response.context['accounts']
        self.assertEqual(accounts, [self.bank, self.wallet])
        self.assertEqual(accounts[0].current_balance, Decimal('2879.75'))
        self.assertEqual(accounts[1].current_balance, Decimal('320.50'))

    def test_page_renders_kpis_in_reais(self):
        response = self.get_dashboard()

        self.assertContains(response, 'R$ 3.200,25')
        self.assertContains(response, '+ R$ 3.234,56')
        self.assertContains(response, '− R$ 1.534,81')
        self.assertContains(response, '+ R$ 1.699,75')
        self.assertContains(response, 'R$ 2.879,75')
        self.assertContains(response, 'R$ 320,50')

    def test_page_names_the_current_month(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['current_month'], 'março de 2026')
        self.assertContains(response, 'Resumo de março de 2026')


class DashboardMonthResultTests(DashboardTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner, 'Banco Alfa', '1000.00')

    def test_negative_month_result(self):
        create_transaction(
            self.account, self.income_category, '100.00', TODAY
        )
        create_transaction(
            self.account, self.expense_category, '350.75', TODAY
        )

        response = self.get_dashboard()

        self.assertEqual(response.context['month_result'], Decimal('-250.75'))
        self.assertEqual(
            response.context['month_result_abs'], Decimal('250.75')
        )
        self.assertContains(response, '− R$ 250,75')

    def test_month_result_is_zero_when_income_equals_expense(self):
        create_transaction(
            self.account, self.income_category, '42.50', TODAY
        )
        create_transaction(
            self.account, self.expense_category, '42.50', TODAY
        )

        response = self.get_dashboard()

        self.assertEqual(response.context['month_result'], Decimal('0.00'))

    def test_month_totals_keep_exact_cents(self):
        for _ in range(3):
            create_transaction(
                self.account, self.income_category, '0.10', TODAY
            )

        response = self.get_dashboard()

        self.assertEqual(str(response.context['month_income']), '0.30')
        self.assertEqual(str(response.context['total_balance']), '1000.30')

    def test_expense_above_balance_gives_negative_total_balance(self):
        create_transaction(
            self.account, self.expense_category, '1050.00', TODAY
        )

        response = self.get_dashboard()

        self.assertEqual(response.context['total_balance'], Decimal('-50.00'))
        self.assertContains(response, '− R$ 50,00')


class DashboardMonthBoundaryTests(DashboardTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner, 'Banco Alfa', '1000.00')
        create_transaction(
            cls.account, cls.expense_category, '40.00', date(2025, 12, 31)
        )
        create_transaction(
            cls.account, cls.expense_category, '15.00', date(2026, 1, 1)
        )
        create_transaction(
            cls.account, cls.income_category, '100.00', date(2026, 1, 31)
        )
        create_transaction(
            cls.account, cls.income_category, '200.00', date(2026, 2, 1)
        )

    def assert_month_totals(self, today, income, expense):
        response = self.get_dashboard(today)

        self.assertEqual(response.context['month_income'], Decimal(income))
        self.assertEqual(response.context['month_expense'], Decimal(expense))
        # 1000,00 + 100,00 + 200,00 - 40,00 - 15,00: não depende da data.
        self.assertEqual(response.context['total_balance'], Decimal('1245.00'))

    def test_last_day_of_month_counts_only_that_month(self):
        self.assert_month_totals(date(2026, 1, 31), '100.00', '15.00')

    def test_first_day_of_month_counts_only_the_new_month(self):
        self.assert_month_totals(date(2026, 2, 1), '200.00', '0.00')

    def test_last_day_of_year_counts_only_december(self):
        self.assert_month_totals(date(2025, 12, 31), '0.00', '40.00')

    def test_first_day_of_year_counts_only_january(self):
        self.assert_month_totals(date(2026, 1, 1), '100.00', '15.00')

    def test_month_follows_local_date_instead_of_utc(self):
        # 02:00 UTC de 01/02 ainda é 23:00 de 31/01 em America/Sao_Paulo.
        utc_now = datetime(2026, 2, 1, 2, 0, tzinfo=UTC)

        with patch('core.views.timezone.now', return_value=utc_now):
            response = self.client.get(self.dashboard_url)

        self.assertEqual(response.context['month_income'], Decimal('100.00'))
        self.assertEqual(response.context['month_expense'], Decimal('15.00'))
        self.assertEqual(
            response.context['current_month'], 'janeiro de 2026'
        )


class DashboardLatestTransactionsTests(DashboardTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner, 'Banco Alfa', '1000.00')

    def create_dated_transactions(self, days):
        return {
            day: create_transaction(
                self.account,
                self.expense_category,
                '10.00',
                date(2026, 3, day),
                f'Compra do dia {day}',
            )
            for day in days
        }

    def test_shows_only_the_five_most_recent_transactions(self):
        # Criadas fora de ordem para que a data decida, não a criação.
        created = self.create_dated_transactions([3, 7, 1, 6, 2, 5, 4])

        response = self.get_dashboard()

        self.assertEqual(
            list(response.context['latest_transactions']),
            [created[7], created[6], created[5], created[4], created[3]],
        )
        self.assertContains(response, 'Compra do dia 3')
        self.assertNotContains(response, 'Compra do dia 2')
        self.assertNotContains(response, 'Compra do dia 1')

    def test_shows_all_transactions_when_there_are_fewer_than_five(self):
        created = self.create_dated_transactions([1, 2])

        response = self.get_dashboard()

        self.assertEqual(
            list(response.context['latest_transactions']),
            [created[2], created[1]],
        )

    def test_includes_transactions_from_other_months(self):
        previous = create_transaction(
            self.account,
            self.income_category,
            '500.00',
            date(2025, 11, 20),
            'Entrada antiga',
        )

        response = self.get_dashboard()

        self.assertEqual(
            list(response.context['latest_transactions']), [previous]
        )
        self.assertEqual(response.context['month_income'], Decimal('0.00'))

    def test_same_date_shows_latest_created_first(self):
        first = create_transaction(
            self.account, self.expense_category, '10.00', TODAY
        )
        second = create_transaction(
            self.account, self.expense_category, '20.00', TODAY
        )
        # O relógio do Windows pode repetir o instante entre dois inserts.
        Transaction.objects.filter(pk=first.pk).update(
            created_at=datetime(2026, 3, 15, 10, 0, tzinfo=UTC)
        )
        Transaction.objects.filter(pk=second.pk).update(
            created_at=datetime(2026, 3, 15, 11, 0, tzinfo=UTC)
        )

        response = self.get_dashboard()

        self.assertEqual(
            list(response.context['latest_transactions']), [second, first]
        )


class DashboardIsolationTests(DashboardTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner, 'Banco Alfa', '1000.00')
        cls.transaction = create_transaction(
            cls.account,
            cls.income_category,
            '200.00',
            TODAY,
            'Lançamento da dona',
        )
        cls.other_account = create_account(
            cls.other_user, 'Conta do outro', '9000.00'
        )
        cls.other_transaction = create_transaction(
            cls.other_account,
            create_category(
                cls.other_user, Category.CategoryType.INCOME, 'Bônus'
            ),
            '700.00',
            TODAY,
            'Lançamento do outro',
        )
        create_transaction(
            cls.other_account,
            create_category(
                cls.other_user, Category.CategoryType.EXPENSE, 'Lazer'
            ),
            '300.00',
            TODAY,
            'Despesa do outro',
        )

    def test_other_user_data_does_not_change_kpis(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['total_balance'], Decimal('1200.00'))
        self.assertEqual(response.context['month_income'], Decimal('200.00'))
        self.assertEqual(response.context['month_expense'], Decimal('0.00'))
        self.assertEqual(response.context['month_result'], Decimal('200.00'))

    def test_other_user_data_does_not_appear_in_lists(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['accounts'], [self.account])
        self.assertEqual(
            list(response.context['latest_transactions']), [self.transaction]
        )
        self.assertNotContains(response, 'Conta do outro')
        self.assertNotContains(response, 'Lançamento do outro')

    def test_each_user_sees_their_own_kpis(self):
        self.client.force_login(self.other_user)

        response = self.get_dashboard()

        # 9000,00 + 700,00 - 300,00 = 9400,00; resultado 700,00 - 300,00.
        self.assertEqual(response.context['total_balance'], Decimal('9400.00'))
        self.assertEqual(response.context['month_income'], Decimal('700.00'))
        self.assertEqual(response.context['month_expense'], Decimal('300.00'))
        self.assertEqual(response.context['month_result'], Decimal('400.00'))
        self.assertEqual(response.context['accounts'], [self.other_account])
        self.assertNotContains(response, 'Lançamento da dona')


class DashboardEmptyStateTests(DashboardTestCase):
    def test_user_without_data_receives_zeros(self):
        response = self.get_dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_balance'], Decimal('0.00'))
        self.assertEqual(response.context['month_income'], Decimal('0.00'))
        self.assertEqual(response.context['month_expense'], Decimal('0.00'))
        self.assertEqual(response.context['month_result'], Decimal('0.00'))
        self.assertEqual(response.context['month_result_abs'], Decimal('0.00'))

    def test_user_without_data_receives_empty_lists(self):
        response = self.get_dashboard()

        self.assertEqual(response.context['accounts'], [])
        self.assertEqual(list(response.context['latest_transactions']), [])

    def test_user_without_data_sees_empty_states_and_zero_values(self):
        response = self.get_dashboard()

        self.assertContains(response, 'R$ 0,00')
        self.assertContains(
            response, 'Você ainda não registrou nenhuma transação.'
        )
        self.assertContains(
            response, 'Você ainda não cadastrou nenhuma conta.'
        )

    def test_account_without_transactions_counts_only_initial_balance(self):
        account = create_account(self.owner, 'Banco Alfa', '750.25')

        response = self.get_dashboard()

        self.assertEqual(response.context['accounts'], [account])
        self.assertEqual(response.context['total_balance'], Decimal('750.25'))
        self.assertEqual(response.context['month_income'], Decimal('0.00'))
        self.assertEqual(response.context['month_expense'], Decimal('0.00'))
        self.assertEqual(response.context['month_result'], Decimal('0.00'))
