from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.base import Message
from django.contrib.messages.test import MessagesTestMixin
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from categories.models import Category
from transactions.forms import TransactionFilterForm, TransactionForm
from transactions.models import Transaction

User = get_user_model()

AMOUNT_ERROR = 'O valor deve ser maior que zero.'
CATEGORY_TYPE_ERROR = 'A categoria deve ser do mesmo tipo da transação.'
INCOME = Transaction.TransactionType.INCOME
EXPENSE = Transaction.TransactionType.EXPENSE


def create_account(user, name='Conta corrente principal'):
    return Account.objects.create(
        user=user,
        name=name,
        initial_balance=Decimal('1000.00'),
    )


def create_category(user, name, category_type):
    return Category.objects.create(
        user=user,
        name=name,
        category_type=category_type,
    )


def create_transaction(account, category, **kwargs):
    defaults = {
        'transaction_type': category.category_type,
        'amount': Decimal('100.00'),
        'date': date(2026, 3, 15),
        'description': 'Lançamento original',
    }
    defaults.update(kwargs)
    return Transaction.objects.create(
        user=account.user,
        account=account,
        category=category,
        **defaults,
    )


class TransactionTestCase(MessagesTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email='dono@finanpy.test',
            password='SenhaForte!123',
        )
        cls.other_user = User.objects.create_user(
            email='outro@finanpy.test',
            password='SenhaForte!123',
        )
        cls.account = create_account(cls.owner)
        cls.income_category = create_category(cls.owner, 'Salário', INCOME)
        cls.expense_category = create_category(cls.owner, 'Mercado', EXPENSE)
        cls.list_url = reverse('transactions:list')
        cls.create_url = reverse('transactions:create')

    def setUp(self):
        self.client.force_login(self.owner)

    def build_payload(self, **kwargs):
        payload = {
            'transaction_type': INCOME,
            'amount': '234.56',
            'date': '2026-03-10',
            'description': 'Salário de março',
            'account': self.account.pk,
            'category': self.income_category.pk,
        }
        payload.update(kwargs)
        return payload


class TransactionCrudTests(TransactionTestCase):
    def test_list_shows_owner_transaction_details(self):
        transaction = create_transaction(
            self.account,
            self.income_category,
            amount=Decimal('1234.56'),
            description='Salário de março',
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_list.html')
        self.assertEqual(list(response.context['transactions']), [transaction])
        self.assertContains(response, 'Salário de março')
        self.assertContains(response, 'Conta corrente principal')
        self.assertContains(response, '15/03/2026')
        self.assertContains(response, '+ R$ 1.234,56')

    def test_list_shows_expense_with_minus_sign(self):
        create_transaction(
            self.account,
            self.expense_category,
            amount=Decimal('34.56'),
        )

        response = self.client.get(self.list_url)

        self.assertContains(response, '− R$ 34,56')

    def test_list_orders_from_most_recent_to_oldest(self):
        oldest = create_transaction(
            self.account,
            self.income_category,
            date=date(2026, 1, 5),
        )
        newest = create_transaction(
            self.account,
            self.income_category,
            date=date(2026, 3, 5),
        )
        middle = create_transaction(
            self.account,
            self.income_category,
            date=date(2026, 2, 5),
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            list(response.context['transactions']),
            [newest, middle, oldest],
        )

    def test_list_without_transactions_shows_empty_state(self):
        response = self.client.get(self.list_url)

        self.assertContains(
            response,
            'Você ainda não registrou nenhuma transação.',
        )

    def test_create_page_renders_form(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_form.html')

    def test_create_saves_transaction_and_redirects_with_message(self):
        response = self.client.post(self.create_url, self.build_payload())

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Transação registrada com sucesso.')],
        )
        transaction = Transaction.objects.get()
        self.assertEqual(transaction.transaction_type, INCOME)
        self.assertEqual(transaction.amount, Decimal('234.56'))
        self.assertEqual(transaction.date, date(2026, 3, 10))
        self.assertEqual(transaction.description, 'Salário de março')
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.income_category)

    def test_created_transaction_belongs_to_request_user(self):
        self.client.post(
            self.create_url,
            self.build_payload(user=self.other_user.pk),
        )

        self.assertEqual(Transaction.objects.get().user, self.owner)

    def test_create_with_invalid_data_saves_nothing(self):
        response = self.client.post(
            self.create_url,
            self.build_payload(description=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('description', response.context['form'].errors)
        self.assertFalse(Transaction.objects.exists())

    def test_update_page_renders_form_with_transaction_data(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.get(
            reverse('transactions:update', args=[transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_form.html')
        self.assertEqual(response.context['form'].instance, transaction)

    def test_update_saves_changes_and_redirects_with_message(self):
        transaction = create_transaction(self.account, self.income_category)
        other_account = create_account(self.owner, name='Poupança')

        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            self.build_payload(
                transaction_type=EXPENSE,
                amount='34.56',
                date='2026-04-20',
                description='Compra do mês',
                account=other_account.pk,
                category=self.expense_category.pk,
            ),
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Transação atualizada com sucesso.')],
        )
        transaction.refresh_from_db()
        self.assertEqual(transaction.transaction_type, EXPENSE)
        self.assertEqual(transaction.amount, Decimal('34.56'))
        self.assertEqual(transaction.date, date(2026, 4, 20))
        self.assertEqual(transaction.description, 'Compra do mês')
        self.assertEqual(transaction.account, other_account)
        self.assertEqual(transaction.category, self.expense_category)
        self.assertEqual(transaction.user, self.owner)

    def test_delete_page_asks_for_confirmation_without_deleting(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.get(
            reverse('transactions:delete', args=[transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'transactions/transaction_confirm_delete.html',
        )
        self.assertTrue(
            Transaction.objects.filter(pk=transaction.pk).exists()
        )

    def test_delete_removes_transaction_and_redirects_with_message(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.post(
            reverse('transactions:delete', args=[transaction.pk])
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Transação excluída com sucesso.')],
        )
        self.assertFalse(
            Transaction.objects.filter(pk=transaction.pk).exists()
        )

    def test_success_message_is_displayed_on_list_page(self):
        response = self.client.post(
            self.create_url,
            self.build_payload(),
            follow=True,
        )

        self.assertContains(response, 'Transação registrada com sucesso.')


class TransactionAmountValidationTests(TransactionTestCase):
    def test_create_rejects_zero_and_negative_amounts(self):
        for amount in ('0', '0.00', '-0.01', '-50.00'):
            with self.subTest(amount=amount):
                response = self.client.post(
                    self.create_url,
                    self.build_payload(amount=amount),
                )

                self.assertEqual(response.status_code, 200)
                self.assertFormError(
                    response.context['form'],
                    'amount',
                    AMOUNT_ERROR,
                )
                self.assertFalse(Transaction.objects.exists())

    def test_create_accepts_minimum_amount(self):
        response = self.client.post(
            self.create_url,
            self.build_payload(amount='0.01'),
        )

        self.assertRedirects(response, self.list_url)
        self.assertEqual(Transaction.objects.get().amount, Decimal('0.01'))

    def test_update_rejects_zero_and_keeps_transaction(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            self.build_payload(amount='0.00'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'amount',
            AMOUNT_ERROR,
        )
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.description, 'Lançamento original')


class TransactionCategoryTypeTests(TransactionTestCase):
    def test_create_rejects_category_of_different_type(self):
        combinations = (
            (INCOME, self.expense_category),
            (EXPENSE, self.income_category),
        )
        for transaction_type, category in combinations:
            with self.subTest(transaction_type=transaction_type):
                response = self.client.post(
                    self.create_url,
                    self.build_payload(
                        transaction_type=transaction_type,
                        category=category.pk,
                    ),
                )

                self.assertEqual(response.status_code, 200)
                self.assertFormError(
                    response.context['form'],
                    'category',
                    CATEGORY_TYPE_ERROR,
                )
                self.assertContains(response, CATEGORY_TYPE_ERROR)
                self.assertFalse(Transaction.objects.exists())

    def test_create_accepts_category_of_same_type(self):
        combinations = (
            (INCOME, self.income_category),
            (EXPENSE, self.expense_category),
        )
        for transaction_type, category in combinations:
            with self.subTest(transaction_type=transaction_type):
                response = self.client.post(
                    self.create_url,
                    self.build_payload(
                        transaction_type=transaction_type,
                        category=category.pk,
                    ),
                )

                self.assertRedirects(response, self.list_url)
                transaction = Transaction.objects.get(
                    transaction_type=transaction_type,
                )
                self.assertEqual(transaction.category, category)

    def test_update_rejects_type_change_that_diverges_from_category(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            self.build_payload(
                transaction_type=EXPENSE,
                category=self.income_category.pk,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'category',
            CATEGORY_TYPE_ERROR,
        )
        transaction.refresh_from_db()
        self.assertEqual(transaction.transaction_type, INCOME)
        self.assertEqual(transaction.description, 'Lançamento original')


class TransactionFormOwnershipTests(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.foreign_account = create_account(
            cls.other_user,
            name='Conta alheia',
        )
        cls.foreign_category = create_category(
            cls.other_user,
            'Categoria alheia',
            INCOME,
        )

    def assert_invalid_choice(self, form, field):
        self.assertEqual(
            [error.code for error in form.errors.as_data()[field]],
            ['invalid_choice'],
        )

    def assert_only_owner_options(self, form):
        self.assertCountEqual(form.fields['account'].queryset, [self.account])
        self.assertCountEqual(
            form.fields['category'].queryset,
            [self.income_category, self.expense_category],
        )

    def test_form_querysets_only_have_user_objects(self):
        self.assert_only_owner_options(TransactionForm(user=self.owner))

    def test_form_category_choices_are_grouped_with_user_objects(self):
        form = TransactionForm(user=self.owner)

        self.assertEqual(
            form.fields['category'].choices,
            [
                ('', 'Selecione a categoria'),
                ('Entradas', [(self.income_category.pk, 'Salário')]),
                ('Saídas', [(self.expense_category.pk, 'Mercado')]),
            ],
        )

    def test_create_page_does_not_render_objects_of_other_user(self):
        response = self.client.get(self.create_url)

        self.assert_only_owner_options(response.context['form'])
        self.assertContains(response, 'Conta corrente principal')
        self.assertContains(response, 'Salário')
        self.assertNotContains(response, 'Conta alheia')
        self.assertNotContains(response, 'Categoria alheia')

    def test_update_page_does_not_render_objects_of_other_user(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.get(
            reverse('transactions:update', args=[transaction.pk])
        )

        self.assert_only_owner_options(response.context['form'])
        self.assertNotContains(response, 'Conta alheia')
        self.assertNotContains(response, 'Categoria alheia')

    def test_create_rejects_account_of_other_user(self):
        response = self.client.post(
            self.create_url,
            self.build_payload(account=self.foreign_account.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assert_invalid_choice(response.context['form'], 'account')
        self.assertFalse(Transaction.objects.exists())

    def test_create_rejects_category_of_other_user(self):
        response = self.client.post(
            self.create_url,
            self.build_payload(category=self.foreign_category.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assert_invalid_choice(response.context['form'], 'category')
        self.assertFalse(Transaction.objects.exists())

    def test_update_rejects_account_and_category_of_other_user(self):
        transaction = create_transaction(self.account, self.income_category)

        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            self.build_payload(
                account=self.foreign_account.pk,
                category=self.foreign_category.pk,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assert_invalid_choice(response.context['form'], 'account')
        self.assert_invalid_choice(response.context['form'], 'category')
        transaction.refresh_from_db()
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.income_category)

    def test_filter_form_querysets_only_have_user_objects(self):
        self.assert_only_owner_options(TransactionFilterForm(user=self.owner))

    def test_filter_form_rejects_objects_of_other_user(self):
        form = TransactionFilterForm(
            {
                'account': self.foreign_account.pk,
                'category': self.foreign_category.pk,
            },
            user=self.owner,
        )

        self.assertFalse(form.is_valid())
        self.assert_invalid_choice(form, 'account')
        self.assert_invalid_choice(form, 'category')

    def test_filter_bar_does_not_render_objects_of_other_user(self):
        create_transaction(self.account, self.income_category)

        response = self.client.get(self.list_url)

        self.assert_only_owner_options(response.context['filter_form'])
        self.assertNotContains(response, 'Conta alheia')
        self.assertNotContains(response, 'Categoria alheia')

    def test_list_filtered_by_foreign_account_exposes_no_foreign_data(self):
        own = create_transaction(self.account, self.income_category)
        create_transaction(
            self.foreign_account,
            self.foreign_category,
            description='Lançamento alheio',
        )

        response = self.client.get(
            self.list_url,
            {'account': self.foreign_account.pk},
        )

        self.assert_invalid_choice(response.context['filter_form'], 'account')
        self.assertEqual(list(response.context['transactions']), [own])
        self.assertNotContains(response, 'Lançamento alheio')


class TransactionFilterTests(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.savings = create_account(cls.owner, name='Poupança')
        cls.freelance = create_category(cls.owner, 'Freela', INCOME)
        cls.rent = create_category(cls.owner, 'Aluguel', EXPENSE)
        cls.feb_freelance = create_transaction(
            cls.account,
            cls.freelance,
            amount=Decimal('500.00'),
            date=date(2026, 2, 28),
        )
        cls.mar_salary = create_transaction(
            cls.account,
            cls.income_category,
            amount=Decimal('1000.00'),
            date=date(2026, 3, 1),
        )
        cls.mar_market = create_transaction(
            cls.account,
            cls.expense_category,
            amount=Decimal('200.50'),
            date=date(2026, 3, 10),
        )
        cls.mar_rent = create_transaction(
            cls.savings,
            cls.rent,
            amount=Decimal('300.25'),
            date=date(2026, 3, 20),
        )
        cls.mar_freelance = create_transaction(
            cls.savings,
            cls.freelance,
            amount=Decimal('150.75'),
            date=date(2026, 3, 31),
        )
        cls.apr_market = create_transaction(
            cls.account,
            cls.expense_category,
            amount=Decimal('49.99'),
            date=date(2026, 4, 1),
        )
        # Lançamento de outro usuário na mesma faixa de datas: nunca pode
        # aparecer na lista nem somar nos totais.
        create_transaction(
            create_account(cls.other_user, name='Conta alheia'),
            create_category(cls.other_user, 'Categoria alheia', INCOME),
            amount=Decimal('9999.99'),
            date=date(2026, 3, 10),
        )

    def assert_filter_result(self, params, expected, income, expense):
        response = self.client.get(self.list_url, params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filter_form'].errors, {})
        self.assertEqual(list(response.context['transactions']), expected)
        self.assertEqual(response.context['total_income'], Decimal(income))
        self.assertEqual(response.context['total_expense'], Decimal(expense))
        return response

    def test_without_filters_lists_everything_from_the_user(self):
        self.assert_filter_result(
            {},
            [
                self.apr_market,
                self.mar_freelance,
                self.mar_rent,
                self.mar_market,
                self.mar_salary,
                self.feb_freelance,
            ],
            '1650.75',
            '550.74',
        )

    def test_start_date_is_inclusive(self):
        self.assert_filter_result(
            {'start_date': '2026-03-31'},
            [self.apr_market, self.mar_freelance],
            '150.75',
            '49.99',
        )

    def test_end_date_is_inclusive(self):
        self.assert_filter_result(
            {'end_date': '2026-03-01'},
            [self.mar_salary, self.feb_freelance],
            '1500.00',
            '0.00',
        )

    def test_period_includes_both_limits_and_excludes_outside(self):
        self.assert_filter_result(
            {'start_date': '2026-03-01', 'end_date': '2026-03-31'},
            [
                self.mar_freelance,
                self.mar_rent,
                self.mar_market,
                self.mar_salary,
            ],
            '1150.75',
            '500.75',
        )

    def test_period_of_a_single_day(self):
        self.assert_filter_result(
            {'start_date': '2026-03-10', 'end_date': '2026-03-10'},
            [self.mar_market],
            '0.00',
            '200.50',
        )

    def test_filter_by_income_type(self):
        self.assert_filter_result(
            {'transaction_type': INCOME},
            [self.mar_freelance, self.mar_salary, self.feb_freelance],
            '1650.75',
            '0.00',
        )

    def test_filter_by_expense_type(self):
        self.assert_filter_result(
            {'transaction_type': EXPENSE},
            [self.apr_market, self.mar_rent, self.mar_market],
            '0.00',
            '550.74',
        )

    def test_filter_by_account(self):
        self.assert_filter_result(
            {'account': self.savings.pk},
            [self.mar_freelance, self.mar_rent],
            '150.75',
            '300.25',
        )

    def test_filter_by_category(self):
        self.assert_filter_result(
            {'category': self.expense_category.pk},
            [self.apr_market, self.mar_market],
            '0.00',
            '250.49',
        )

    def test_filters_combine_period_and_account(self):
        self.assert_filter_result(
            {
                'start_date': '2026-03-01',
                'end_date': '2026-03-31',
                'account': self.account.pk,
            },
            [self.mar_market, self.mar_salary],
            '1000.00',
            '200.50',
        )

    def test_all_filters_combined(self):
        self.assert_filter_result(
            {
                'start_date': '2026-03-01',
                'end_date': '2026-03-31',
                'transaction_type': EXPENSE,
                'account': self.account.pk,
                'category': self.expense_category.pk,
            },
            [self.mar_market],
            '0.00',
            '200.50',
        )

    def test_combination_without_result_shows_empty_state(self):
        response = self.assert_filter_result(
            {
                'transaction_type': INCOME,
                'category': self.expense_category.pk,
            },
            [],
            '0.00',
            '0.00',
        )

        self.assertContains(
            response,
            'Nenhuma transação encontrada para os filtros selecionados.',
        )

    def test_totals_of_filtered_result_are_displayed(self):
        response = self.assert_filter_result(
            {'start_date': '2026-03-01', 'end_date': '2026-03-31'},
            [
                self.mar_freelance,
                self.mar_rent,
                self.mar_market,
                self.mar_salary,
            ],
            '1150.75',
            '500.75',
        )

        self.assertContains(response, '+ R$ 1.150,75')
        self.assertContains(response, '− R$ 500,75')

    def test_totals_consider_all_pages_of_the_filtered_result(self):
        for day in range(1, 22):
            create_transaction(
                self.account,
                self.income_category,
                amount=Decimal('10.00'),
                date=date(2026, 5, day),
            )
        params = {'start_date': '2026-05-01', 'end_date': '2026-05-31'}

        for page, page_size in ((1, 20), (2, 1)):
            with self.subTest(page=page):
                response = self.client.get(
                    self.list_url,
                    {**params, 'page': page},
                )

                self.assertEqual(
                    len(response.context['transactions']),
                    page_size,
                )
                self.assertEqual(
                    response.context['total_income'],
                    Decimal('210.00'),
                )
                self.assertEqual(
                    response.context['total_expense'],
                    Decimal('0.00'),
                )

    def test_invalid_date_shows_error_and_keeps_full_list(self):
        response = self.client.get(self.list_url, {'start_date': 'invalida'})

        self.assertIn('start_date', response.context['filter_form'].errors)
        self.assertEqual(len(response.context['transactions']), 6)
        self.assertEqual(
            response.context['total_income'],
            Decimal('1650.75'),
        )


class TransactionIsolationTests(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.transaction = create_transaction(
            cls.account,
            cls.income_category,
            description='Lançamento do dono',
        )
        cls.update_url = reverse(
            'transactions:update',
            args=[cls.transaction.pk],
        )
        cls.delete_url = reverse(
            'transactions:delete',
            args=[cls.transaction.pk],
        )
        cls.other_account = create_account(
            cls.other_user,
            name='Conta do outro',
        )
        cls.other_category = create_category(
            cls.other_user,
            'Categoria do outro',
            EXPENSE,
        )

    def setUp(self):
        self.client.force_login(self.other_user)

    def assert_transaction_unchanged(self):
        transaction = Transaction.objects.get(pk=self.transaction.pk)
        self.assertEqual(transaction.user, self.owner)
        self.assertEqual(transaction.transaction_type, INCOME)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.date, date(2026, 3, 15))
        self.assertEqual(transaction.description, 'Lançamento do dono')
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.income_category)

    def test_list_hides_transactions_from_other_user(self):
        own_transaction = create_transaction(
            self.other_account,
            self.other_category,
            amount=Decimal('25.00'),
            description='Lançamento do outro',
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            list(response.context['transactions']),
            [own_transaction],
        )
        self.assertContains(response, 'Lançamento do outro')
        self.assertNotContains(response, 'Lançamento do dono')

    def test_list_totals_ignore_transactions_from_other_user(self):
        create_transaction(
            self.other_account,
            self.other_category,
            amount=Decimal('25.00'),
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.context['total_income'], Decimal('0.00'))
        self.assertEqual(response.context['total_expense'], Decimal('25.00'))

    def test_get_update_returns_404(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 404)
        self.assert_transaction_unchanged()

    def test_post_update_returns_404_and_keeps_transaction(self):
        response = self.client.post(
            self.update_url,
            self.build_payload(
                transaction_type=EXPENSE,
                amount='1.00',
                date='2026-12-25',
                description='Lançamento invadido',
                account=self.other_account.pk,
                category=self.other_category.pk,
            ),
        )

        self.assertEqual(response.status_code, 404)
        self.assert_transaction_unchanged()

    def test_get_delete_returns_404(self):
        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_transaction_unchanged()

    def test_post_delete_returns_404_and_keeps_transaction(self):
        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_transaction_unchanged()
