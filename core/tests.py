from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Account
from ai.context import calculate_analysis_period
from ai.models import FinancialAnalysis
from ai.services import AnalysisState
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


# Card do assistente (PRD 14.15) -------------------------------------------

AI_TEST_SETTINGS = {
    'OPENAI_API_KEY': 'chave-de-teste-nao-usada',
    'AI_ANALYSIS_WINDOW_MONTHS': 6,
    'AI_ANALYSIS_MIN_TRANSACTIONS': 5,
    'AI_ANALYSIS_DAILY_LIMIT': 3,
    'AI_ANALYSIS_STALE_DAYS': 30,
    'AI_ANALYSIS_PENDING_TIMEOUT_MINUTES': 5,
    'AI_RUN_BUDGET_SECONDS': 120,
}

CARD_TITLE = 'Assistente financeiro'
NO_ANALYSIS_TEXT = (
    'Você ainda não tem análises. Gere a primeira para receber dicas sobre '
    'suas finanças.'
)
RUNNING_TEXT = 'Há uma análise em andamento. Atualize a página em instantes.'
FAILED_TEXT = 'Não foi possível concluir a última análise.'
STALE_TEXT = (
    'Esta análise tem mais de 30 dias. Gere uma nova para refletir seus '
    'dados atuais.'
)
LIMIT_TEXT = (
    'Você atingiu o limite de análises de hoje. Tente novamente amanhã.'
)
INSUFFICIENT_TEXT = 'Registre pelo menos 5 transações para gerar uma análise.'
DISABLED_TEXT = 'O assistente não está disponível no momento.'
LOADING_TEXT = 'Gerando análise... isso pode levar até 2 minutos.'
DISCLAIMER_TEXT = (
    'Conteúdo gerado por inteligência artificial, com caráter educativo, a '
    'partir dos seus lançamentos. Pode conter erros e não substitui '
    'orientação profissional nem constitui recomendação de investimento.'
)
OPENAI_NOTICE_TEXT = (
    'Ao gerar a análise, seus lançamentos financeiros são enviados à OpenAI '
    'para processamento. Nome, e-mail e telefone não são enviados.'
)
GENERATE_FORM = 'id="analysis-form"'


def analysis_item(title):
    return {
        'title': title,
        'description': f'Descrição de {title}.',
        'evidence': [{
            'label': 'Entradas',
            'value': '3000.00',
            'source_tool': 'get_financial_summary',
        }],
    }


def create_analysis(user, status=FinancialAnalysis.Status.SUCCESS, **fields):
    period_start, period_end = calculate_analysis_period()
    if status == FinancialAnalysis.Status.SUCCESS:
        fields.setdefault('generated_at', timezone.now())
        fields.setdefault('main_insight', analysis_item('Insight principal'))
    return FinancialAnalysis.objects.create(
        user=user,
        status=status,
        period_start=period_start,
        period_end=period_end,
        model_name='modelo-falso',
        prompt_version='1',
        **fields,
    )


def move_analysis(analysis, moment, generated=True):
    """Muda created_at (e generated_at) direto no banco."""
    fields = {'created_at': moment}
    if generated:
        fields['generated_at'] = moment
    FinancialAnalysis.objects.filter(pk=analysis.pk).update(**fields)


class AgentNotCalledMixin:
    """Falha o teste se o dashboard chegar ao agente ou ao serviço."""

    def setUp(self):
        super().setUp()
        self.agent_mocks = []
        for target in (
            'ai.agent.build_chat_model',
            'ai.agent.run_agent',
            'ai.services.generate_analysis',
            'ai.views.generate_analysis',
        ):
            patcher = patch(target)
            self.agent_mocks.append(patcher.start())
            self.addCleanup(patcher.stop)

    def tearDown(self):
        for mocked in self.agent_mocks:
            mocked.assert_not_called()
        super().tearDown()


@override_settings(**AI_TEST_SETTINGS)
class DashboardAnalysisCardTests(AgentNotCalledMixin, TestCase):
    """Cada estado do card, com a data real: os limites diários usam o
    relógio do banco, e congelar só localdate os desencontraria.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email='card@finanpy.test',
            password='SenhaForte!123',
            first_name='Dona',
        )
        cls.other_user = User.objects.create_user(
            email='card.outro@finanpy.test',
            password='SenhaForte!123',
        )
        cls.account = create_account(cls.owner, 'Banco Alfa', '1000.00')
        cls.income_category = create_category(
            cls.owner, Category.CategoryType.INCOME, 'Salário'
        )
        cls.expense_category = create_category(
            cls.owner, Category.CategoryType.EXPENSE, 'Mercado'
        )
        cls.dashboard_url = reverse('dashboard')

    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def create_transactions(self, count):
        today = timezone.localdate()
        for _ in range(count):
            create_transaction(
                self.account, self.expense_category, '10.00', today
            )

    def get_card(self, expected_state):
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'components/analysis_card.html')
        state = response.context['analysis_state']
        self.assertEqual(state['state'], expected_state)
        self.assertContains(response, CARD_TITLE)
        return response, state

    def test_context_has_the_documented_keys(self):
        self.create_transactions(5)

        response, state = self.get_card(AnalysisState.NO_ANALYSIS)

        self.assertEqual(
            set(state),
            {
                'state',
                'analysis',
                'is_stale',
                'notices',
                'can_generate',
                'loading_message',
            },
        )

    def test_no_analysis(self):
        self.create_transactions(5)

        response, state = self.get_card(AnalysisState.NO_ANALYSIS)

        self.assertIsNone(state['analysis'])
        self.assertEqual(state['notices'], [NO_ANALYSIS_TEXT])
        self.assertTrue(state['can_generate'])
        self.assertContains(response, NO_ANALYSIS_TEXT)
        self.assertContains(response, GENERATE_FORM)
        self.assertContains(response, reverse('ai:create'))
        self.assertContains(response, 'Gerar análise')
        self.assertContains(response, OPENAI_NOTICE_TEXT)
        self.assertNotContains(response, 'Ver análise completa')

    def test_with_analysis(self):
        self.create_transactions(5)
        yesterday = timezone.localdate() - timedelta(days=1)
        generated_at = timezone.make_aware(
            datetime.combine(yesterday, time(14, 30))
        )
        analysis = create_analysis(
            self.owner,
            alerts=[{
                **analysis_item('Alerta crítico'),
                'severity': 'critical',
            }],
            recommendations=[
                analysis_item(f'Recomendação {number}')
                for number in (1, 2, 3, 4)
            ],
        )
        move_analysis(analysis, generated_at)
        create_analysis(
            self.other_user,
            main_insight=analysis_item('Insight do outro'),
        )
        period_start, period_end = calculate_analysis_period()

        response, state = self.get_card(AnalysisState.WITH_ANALYSIS)

        self.assertEqual(state['analysis'], analysis)
        self.assertEqual(state['notices'], [])
        self.assertTrue(state['can_generate'])
        self.assertContains(
            response,
            f'Período analisado: {period_start:%d/%m/%Y} a '
            f'{period_end:%d/%m/%Y}',
        )
        self.assertContains(
            response, f'Última análise: {yesterday:%d/%m/%Y} às 14:30'
        )
        self.assertContains(response, 'Insight principal')
        self.assertContains(response, 'Alerta crítico')
        # Até 3 recomendações no card.
        self.assertContains(response, 'Recomendação 3')
        self.assertNotContains(response, 'Recomendação 4')
        self.assertContains(response, 'Ver análise completa')
        self.assertContains(
            response, reverse('ai:detail', args=[analysis.pk])
        )
        self.assertContains(response, 'Ver histórico')
        self.assertContains(response, 'Gerar nova análise')
        self.assertContains(response, DISCLAIMER_TEXT)
        self.assertNotContains(response, 'Insight do outro')

    def test_loading_message_is_ready_for_the_browser(self):
        self.create_transactions(5)

        response, state = self.get_card(AnalysisState.NO_ANALYSIS)

        # O estado Carregando é do navegador: o servidor entrega o texto.
        self.assertEqual(state['loading_message'], LOADING_TEXT)
        self.assertContains(
            response, f'data-loading-message="{LOADING_TEXT}"'
        )
        self.assertContains(response, 'js/analysis_form.js')

    @override_settings(AI_RUN_BUDGET_SECONDS=150)
    def test_loading_message_follows_the_settings(self):
        self.create_transactions(5)

        response, state = self.get_card(AnalysisState.NO_ANALYSIS)

        # 150 s arredondados para cima: 3 minutos.
        self.assertEqual(
            state['loading_message'],
            'Gerando análise... isso pode levar até 3 minutos.',
        )

    def test_running_keeps_the_last_valid_analysis(self):
        self.create_transactions(5)
        valid = create_analysis(self.owner)
        move_analysis(valid, timezone.now() - timedelta(days=2))
        create_analysis(self.owner, status=FinancialAnalysis.Status.PENDING)

        response, state = self.get_card(AnalysisState.RUNNING)

        self.assertEqual(state['analysis'], valid)
        self.assertFalse(state['can_generate'])
        self.assertEqual(state['notices'], [RUNNING_TEXT])
        self.assertContains(response, RUNNING_TEXT)
        self.assertContains(response, 'Insight principal')
        self.assertNotContains(response, GENERATE_FORM)
        self.assertContains(response, 'type="button" disabled')

    def test_old_pending_is_not_running(self):
        self.create_transactions(5)
        pending = create_analysis(
            self.owner, status=FinancialAnalysis.Status.PENDING
        )
        move_analysis(
            pending, timezone.now() - timedelta(days=2), generated=False
        )

        response, state = self.get_card(AnalysisState.NO_ANALYSIS)

        # Ler o dashboard não grava: quem encerra é generate_analysis.
        pending.refresh_from_db()
        self.assertEqual(pending.status, FinancialAnalysis.Status.PENDING)

    def test_failure_keeps_the_last_valid_analysis(self):
        self.create_transactions(5)
        valid = create_analysis(self.owner)
        move_analysis(valid, timezone.now() - timedelta(days=2))
        create_analysis(
            self.owner,
            status=FinancialAnalysis.Status.FAILED,
            error_code=FinancialAnalysis.ErrorCode.TIMEOUT,
        )

        response, state = self.get_card(AnalysisState.FAILED)

        self.assertEqual(state['analysis'], valid)
        self.assertTrue(state['can_generate'])
        self.assertEqual(state['notices'], [FAILED_TEXT])
        self.assertContains(response, FAILED_TEXT)
        self.assertContains(response, 'Insight principal')
        self.assertContains(response, GENERATE_FORM)
        # Detalhes técnicos nunca aparecem.
        self.assertNotContains(response, 'timeout')
        self.assertNotContains(response, 'Tempo esgotado')

    def test_failure_older_than_the_valid_analysis_is_ignored(self):
        self.create_transactions(5)
        failure = create_analysis(
            self.owner, status=FinancialAnalysis.Status.FAILED
        )
        move_analysis(
            failure, timezone.now() - timedelta(days=2), generated=False
        )
        create_analysis(self.owner)

        self.get_card(AnalysisState.WITH_ANALYSIS)

    def test_stale_analysis(self):
        self.create_transactions(5)
        analysis = create_analysis(self.owner)
        move_analysis(analysis, timezone.now() - timedelta(days=31))

        response, state = self.get_card(AnalysisState.STALE)

        self.assertTrue(state['is_stale'])
        self.assertTrue(state['can_generate'])
        self.assertEqual(state['notices'], [STALE_TEXT])
        self.assertContains(response, STALE_TEXT)
        self.assertContains(response, 'Insight principal')
        self.assertContains(response, 'Gerar nova análise')

    def test_analysis_of_29_days_is_not_stale(self):
        self.create_transactions(5)
        analysis = create_analysis(self.owner)
        move_analysis(analysis, timezone.now() - timedelta(days=29))

        response, state = self.get_card(AnalysisState.WITH_ANALYSIS)

        self.assertFalse(state['is_stale'])
        self.assertNotContains(response, 'mais de 30 dias')

    def test_limit_reached(self):
        self.create_transactions(5)
        for _ in range(3):
            create_analysis(
                self.owner, status=FinancialAnalysis.Status.FAILED
            )

        response, state = self.get_card(AnalysisState.LIMIT_REACHED)

        self.assertFalse(state['can_generate'])
        self.assertEqual(state['notices'], [LIMIT_TEXT])
        self.assertContains(response, LIMIT_TEXT)
        self.assertNotContains(response, GENERATE_FORM)
        self.assertContains(response, 'type="button" disabled')

    def test_limit_with_a_stale_analysis_keeps_both_notices(self):
        self.create_transactions(5)
        analysis = create_analysis(self.owner)
        move_analysis(analysis, timezone.now() - timedelta(days=40))
        for _ in range(3):
            create_analysis(
                self.owner, status=FinancialAnalysis.Status.FAILED
            )

        response, state = self.get_card(AnalysisState.LIMIT_REACHED)

        # Sem botão, o aviso de desatualizada não convida a gerar.
        self.assertEqual(
            state['notices'],
            [LIMIT_TEXT, 'Esta análise tem mais de 30 dias.'],
        )
        self.assertNotContains(response, GENERATE_FORM)

    def test_insufficient_data(self):
        self.create_transactions(4)

        response, state = self.get_card(AnalysisState.INSUFFICIENT_DATA)

        self.assertFalse(state['can_generate'])
        self.assertEqual(state['notices'], [INSUFFICIENT_TEXT])
        self.assertContains(response, INSUFFICIENT_TEXT)
        self.assertNotContains(response, GENERATE_FORM)
        # Cabeçalho do dashboard e link do card.
        self.assertContains(response, 'Nova transação', count=2)

    @override_settings(AI_ANALYSIS_MIN_TRANSACTIONS=7)
    def test_insufficient_data_reads_the_minimum_from_settings(self):
        self.create_transactions(6)

        response, _ = self.get_card(AnalysisState.INSUFFICIENT_DATA)

        self.assertContains(
            response,
            'Registre pelo menos 7 transações para gerar uma análise.',
        )

    @override_settings(OPENAI_API_KEY='')
    def test_disabled_without_key(self):
        self.create_transactions(5)
        create_analysis(self.owner)

        response, state = self.get_card(AnalysisState.DISABLED)

        self.assertFalse(state['can_generate'])
        self.assertEqual(state['notices'], [DISABLED_TEXT])
        self.assertContains(response, DISABLED_TEXT)
        self.assertNotContains(response, GENERATE_FORM)
        self.assertNotContains(response, OPENAI_NOTICE_TEXT)
        # O restante do dashboard não muda: 1000,00 - 5 x 10,00.
        self.assertEqual(response.context['total_balance'], Decimal('950.00'))
        self.assertEqual(response.context['month_expense'], Decimal('50.00'))
        self.assertContains(response, 'R$ 950,00')

    def test_other_user_analyses_do_not_change_the_state(self):
        self.create_transactions(5)
        for _ in range(3):
            create_analysis(
                self.other_user, status=FinancialAnalysis.Status.FAILED
            )
        create_analysis(
            self.other_user, status=FinancialAnalysis.Status.PENDING
        )

        _, state = self.get_card(AnalysisState.NO_ANALYSIS)

        self.assertIsNone(state['analysis'])


@override_settings(**AI_TEST_SETTINGS)
class DashboardKpiWithAnalysisTests(AgentNotCalledMixin, DashboardKpiTests):
    """Os mesmos KPIs de DashboardKpiTests, agora com análises gravadas.

    O card não pode alterar nenhum cálculo do dashboard (PRD 14.15).
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        create_analysis(cls.owner)
        create_analysis(cls.owner, status=FinancialAnalysis.Status.FAILED)
        create_analysis(cls.owner, status=FinancialAnalysis.Status.PENDING)

    def test_context_still_has_the_analysis_state(self):
        response = self.get_dashboard()

        self.assertIn('analysis_state', response.context)
        self.assertContains(response, CARD_TITLE)


class DashboardDoesNotCallTheModelTests(AgentNotCalledMixin, TestCase):
    @override_settings(**AI_TEST_SETTINGS)
    def test_every_state_loads_without_the_model(self):
        user = User.objects.create_user(
            email='sem.modelo@finanpy.test',
            password='SenhaForte!123',
        )
        account = create_account(user)
        category = create_category(
            user, Category.CategoryType.EXPENSE, 'Mercado'
        )
        self.client.force_login(user)
        url = reverse('dashboard')

        # Sem dados, com dados, com análise e em andamento.
        self.assertEqual(self.client.get(url).status_code, 200)
        for _ in range(5):
            create_transaction(
                account, category, '1.00', timezone.localdate()
            )
        self.assertEqual(self.client.get(url).status_code, 200)
        create_analysis(user)
        self.assertEqual(self.client.get(url).status_code, 200)
        create_analysis(user, status=FinancialAnalysis.Status.PENDING)
        self.assertEqual(self.client.get(url).status_code, 200)
        # tearDown confere que nada chegou ao agente.
