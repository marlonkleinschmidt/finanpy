from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.base import Message
from django.contrib.messages.test import MessagesTestMixin
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction

User = get_user_model()

PROTECTED_MESSAGE = 'Esta conta possui transações e não pode ser excluída.'


def create_account(user, **kwargs):
    defaults = {
        'name': 'Conta corrente principal',
        'bank_name': 'Banco Alfa',
        'account_type': Account.AccountType.CHECKING,
        'initial_balance': Decimal('1000.00'),
    }
    defaults.update(kwargs)
    return Account.objects.create(user=user, **defaults)


def create_transaction(account, transaction_type, category, amount):
    return Transaction.objects.create(
        user=account.user,
        transaction_type=transaction_type,
        amount=amount,
        date=date(2026, 1, 15),
        description='Lançamento de teste',
        account=account,
        category=category,
    )


class AccountTestCase(MessagesTestMixin, TestCase):
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
        cls.list_url = reverse('accounts:list')
        cls.create_url = reverse('accounts:create')


class AccountCrudTests(AccountTestCase):
    def setUp(self):
        self.client.force_login(self.owner)

    def test_list_shows_owner_account_details(self):
        account = create_account(self.owner)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/account_list.html')
        self.assertEqual(list(response.context['accounts']), [account])
        self.assertContains(response, 'Conta corrente principal')
        self.assertContains(response, 'Banco Alfa')

    def test_list_shows_current_balance_in_reais(self):
        account = create_account(self.owner)
        category = Category.objects.create(
            user=self.owner,
            name='Salário',
            category_type=Category.CategoryType.INCOME,
        )
        create_transaction(
            account,
            Transaction.TransactionType.INCOME,
            category,
            Decimal('200.00'),
        )

        response = self.client.get(self.list_url)

        self.assertContains(response, 'R$ 1.200,00')

    def test_create_page_renders_form(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/account_form.html')

    def test_create_saves_account_and_redirects_with_message(self):
        response = self.client.post(
            self.create_url,
            {
                'name': 'Poupança da família',
                'bank_name': 'Banco Beta',
                'account_type': Account.AccountType.SAVINGS,
                'initial_balance': '1500.50',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Conta criada com sucesso.')],
        )
        account = Account.objects.get()
        self.assertEqual(account.name, 'Poupança da família')
        self.assertEqual(account.bank_name, 'Banco Beta')
        self.assertEqual(account.account_type, Account.AccountType.SAVINGS)
        self.assertEqual(account.initial_balance, Decimal('1500.50'))

    def test_created_account_belongs_to_request_user(self):
        self.client.post(
            self.create_url,
            {
                'name': 'Carteira',
                'bank_name': '',
                'account_type': Account.AccountType.WALLET,
                'initial_balance': '10.00',
                'user': self.other_user.pk,
            },
        )

        self.assertEqual(Account.objects.get().user, self.owner)

    def test_create_with_invalid_data_saves_nothing(self):
        response = self.client.post(
            self.create_url,
            {
                'name': '',
                'bank_name': 'Banco Beta',
                'account_type': Account.AccountType.CHECKING,
                'initial_balance': '10.00',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        self.assertFalse(Account.objects.exists())

    def test_update_page_renders_form_with_account_data(self):
        account = create_account(self.owner)

        response = self.client.get(
            reverse('accounts:update', args=[account.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/account_form.html')
        self.assertEqual(response.context['form'].instance, account)

    def test_update_saves_changes_and_redirects_with_message(self):
        account = create_account(self.owner)

        response = self.client.post(
            reverse('accounts:update', args=[account.pk]),
            {
                'name': 'Conta renomeada',
                'bank_name': 'Banco Gama',
                'account_type': Account.AccountType.INVESTMENT,
                'initial_balance': '2500.75',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Conta atualizada com sucesso.')],
        )
        account.refresh_from_db()
        self.assertEqual(account.name, 'Conta renomeada')
        self.assertEqual(account.bank_name, 'Banco Gama')
        self.assertEqual(account.account_type, Account.AccountType.INVESTMENT)
        self.assertEqual(account.initial_balance, Decimal('2500.75'))
        self.assertEqual(account.user, self.owner)

    def test_delete_page_asks_for_confirmation_without_deleting(self):
        account = create_account(self.owner)

        response = self.client.get(
            reverse('accounts:delete', args=[account.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'accounts/account_confirm_delete.html',
        )
        self.assertTrue(Account.objects.filter(pk=account.pk).exists())

    def test_delete_removes_account_and_redirects_with_message(self):
        account = create_account(self.owner)

        response = self.client.post(
            reverse('accounts:delete', args=[account.pk])
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Conta excluída com sucesso.')],
        )
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())

    def test_success_message_is_displayed_on_list_page(self):
        account = create_account(self.owner)

        response = self.client.post(
            reverse('accounts:delete', args=[account.pk]),
            follow=True,
        )

        self.assertContains(response, 'Conta excluída com sucesso.')


class AccountIsolationTests(AccountTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner, name='Conta do dono')
        cls.update_url = reverse('accounts:update', args=[cls.account.pk])
        cls.delete_url = reverse('accounts:delete', args=[cls.account.pk])

    def setUp(self):
        self.client.force_login(self.other_user)

    def assert_account_unchanged(self):
        account = Account.objects.get(pk=self.account.pk)
        self.assertEqual(account.user, self.owner)
        self.assertEqual(account.name, 'Conta do dono')
        self.assertEqual(account.bank_name, 'Banco Alfa')
        self.assertEqual(account.account_type, Account.AccountType.CHECKING)
        self.assertEqual(account.initial_balance, Decimal('1000.00'))

    def test_list_hides_accounts_from_other_user(self):
        own_account = create_account(self.other_user, name='Conta do outro')

        response = self.client.get(self.list_url)

        self.assertEqual(list(response.context['accounts']), [own_account])
        self.assertContains(response, 'Conta do outro')
        self.assertNotContains(response, 'Conta do dono')

    def test_get_update_returns_404(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 404)

    def test_post_update_returns_404_and_keeps_account(self):
        response = self.client.post(
            self.update_url,
            {
                'name': 'Conta invadida',
                'bank_name': 'Banco Invasor',
                'account_type': Account.AccountType.WALLET,
                'initial_balance': '1.00',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assert_account_unchanged()

    def test_get_delete_returns_404(self):
        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_account_unchanged()

    def test_post_delete_returns_404_and_keeps_account(self):
        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_account_unchanged()


class AccountCurrentBalanceTests(AccountTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.income_category = Category.objects.create(
            user=cls.owner,
            name='Salário',
            category_type=Category.CategoryType.INCOME,
        )
        cls.expense_category = Category.objects.create(
            user=cls.owner,
            name='Mercado',
            category_type=Category.CategoryType.EXPENSE,
        )

    def add_income(self, account, amount):
        return create_transaction(
            account,
            Transaction.TransactionType.INCOME,
            self.income_category,
            amount,
        )

    def add_expense(self, account, amount):
        return create_transaction(
            account,
            Transaction.TransactionType.EXPENSE,
            self.expense_category,
            amount,
        )

    def test_account_without_transactions_keeps_initial_balance(self):
        account = create_account(
            self.owner,
            initial_balance=Decimal('1000.00'),
        )

        self.assertEqual(account.current_balance, Decimal('1000.00'))

    def test_balance_sums_income_and_subtracts_expense(self):
        account = create_account(
            self.owner,
            initial_balance=Decimal('1000.00'),
        )
        self.add_income(account, Decimal('234.56'))
        self.add_expense(account, Decimal('34.56'))

        self.assertEqual(account.current_balance, Decimal('1200.00'))

    def test_balance_adds_up_several_transactions_of_each_type(self):
        account = create_account(
            self.owner,
            initial_balance=Decimal('100.10'),
        )
        self.add_income(account, Decimal('0.10'))
        self.add_income(account, Decimal('0.20'))
        self.add_expense(account, Decimal('50.05'))
        self.add_expense(account, Decimal('25.03'))

        self.assertEqual(account.current_balance, Decimal('25.32'))

    def test_balance_with_only_income(self):
        account = create_account(self.owner, initial_balance=Decimal('0.00'))
        self.add_income(account, Decimal('99.99'))

        self.assertEqual(account.current_balance, Decimal('99.99'))

    def test_balance_with_only_expense_can_be_negative(self):
        account = create_account(self.owner, initial_balance=Decimal('10.00'))
        self.add_expense(account, Decimal('25.50'))

        self.assertEqual(account.current_balance, Decimal('-15.50'))

    def test_balance_is_decimal_with_two_places(self):
        account = create_account(
            self.owner,
            initial_balance=Decimal('1000.00'),
        )
        self.add_income(account, Decimal('0.10'))
        self.add_income(account, Decimal('0.20'))

        balance = Account.objects.get(pk=account.pk).current_balance

        self.assertIsInstance(balance, Decimal)
        self.assertEqual(balance.as_tuple().exponent, -2)
        self.assertEqual(balance, Decimal('1000.30'))

    def test_transactions_of_other_account_do_not_interfere(self):
        account = create_account(
            self.owner,
            name='Conta A',
            initial_balance=Decimal('500.00'),
        )
        other_account = create_account(
            self.owner,
            name='Conta B',
            initial_balance=Decimal('50.00'),
        )
        self.add_income(account, Decimal('100.00'))
        self.add_income(other_account, Decimal('7.00'))
        self.add_expense(other_account, Decimal('3.00'))

        self.assertEqual(account.current_balance, Decimal('600.00'))
        self.assertEqual(other_account.current_balance, Decimal('54.00'))


class AccountProtectedDeleteTests(AccountTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = create_account(cls.owner)
        cls.category = Category.objects.create(
            user=cls.owner,
            name='Salário',
            category_type=Category.CategoryType.INCOME,
        )
        cls.transaction = create_transaction(
            cls.account,
            Transaction.TransactionType.INCOME,
            cls.category,
            Decimal('100.00'),
        )
        cls.delete_url = reverse('accounts:delete', args=[cls.account.pk])

    def setUp(self):
        self.client.force_login(self.owner)

    def test_post_delete_keeps_account_and_transaction(self):
        self.client.post(self.delete_url)

        self.assertTrue(Account.objects.filter(pk=self.account.pk).exists())
        self.assertTrue(
            Transaction.objects.filter(pk=self.transaction.pk).exists()
        )

    def test_post_delete_redirects_to_list_with_only_error_message(self):
        response = self.client.post(self.delete_url)

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.ERROR, PROTECTED_MESSAGE)],
        )

    def test_error_message_is_displayed_on_list_page(self):
        response = self.client.post(self.delete_url, follow=True)

        self.assertContains(response, PROTECTED_MESSAGE)
        self.assertNotContains(response, 'Conta excluída com sucesso.')

    def test_model_delete_raises_protected_error(self):
        with self.assertRaises(ProtectedError):
            self.account.delete()

    def test_account_can_be_deleted_after_removing_transactions(self):
        self.transaction.delete()

        response = self.client.post(self.delete_url)

        self.assertRedirects(response, self.list_url)
        self.assertFalse(Account.objects.filter(pk=self.account.pk).exists())
