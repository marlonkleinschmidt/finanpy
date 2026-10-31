from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.base import Message
from django.contrib.messages.test import MessagesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction

User = get_user_model()

DUPLICATE_MESSAGE = 'Você já possui uma categoria com este nome e tipo.'
PROTECTED_MESSAGE = 'Esta categoria possui transações e não pode ser excluída.'


def create_category(user, **kwargs):
    defaults = {
        'name': 'Salário',
        'category_type': Category.CategoryType.INCOME,
        'color': '#10B981',
    }
    defaults.update(kwargs)
    return Category.objects.create(user=user, **defaults)


class CategoryTestCase(MessagesTestMixin, TestCase):
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
        cls.list_url = reverse('categories:list')
        cls.create_url = reverse('categories:create')


class CategoryCrudTests(CategoryTestCase):
    def setUp(self):
        self.client.force_login(self.owner)

    def test_list_shows_owner_categories(self):
        category = create_category(self.owner)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categories/category_list.html')
        self.assertEqual(list(response.context['categories']), [category])
        self.assertContains(response, 'Salário')

    def test_list_separates_income_and_expense_categories(self):
        income = create_category(self.owner, name='Salário')
        expense = create_category(
            self.owner,
            name='Mercado',
            category_type=Category.CategoryType.EXPENSE,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(list(response.context['income_categories']), [income])
        self.assertEqual(
            list(response.context['expense_categories']),
            [expense],
        )

    def test_list_without_categories_shows_empty_state(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Você ainda não cadastrou nenhuma categoria.',
        )

    def test_create_page_renders_form(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categories/category_form.html')

    def test_create_saves_category_and_redirects_with_message(self):
        response = self.client.post(
            self.create_url,
            {
                'name': 'Mercado',
                'category_type': Category.CategoryType.EXPENSE,
                'color': '#EF4444',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Categoria criada com sucesso.')],
        )
        category = Category.objects.get()
        self.assertEqual(category.name, 'Mercado')
        self.assertEqual(
            category.category_type,
            Category.CategoryType.EXPENSE,
        )
        self.assertEqual(category.color, '#EF4444')

    def test_created_category_belongs_to_request_user(self):
        self.client.post(
            self.create_url,
            {
                'name': 'Freelance',
                'category_type': Category.CategoryType.INCOME,
                'color': '#10B981',
                'user': self.other_user.pk,
            },
        )

        self.assertEqual(Category.objects.get().user, self.owner)

    def test_create_with_invalid_data_saves_nothing(self):
        response = self.client.post(
            self.create_url,
            {
                'name': '',
                'category_type': Category.CategoryType.INCOME,
                'color': '#10B981',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        self.assertFalse(Category.objects.exists())

    def test_update_page_renders_form_with_category_data(self):
        category = create_category(self.owner)

        response = self.client.get(
            reverse('categories:update', args=[category.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categories/category_form.html')
        self.assertEqual(response.context['form'].instance, category)

    def test_update_saves_changes_and_redirects_with_message(self):
        category = create_category(self.owner)

        response = self.client.post(
            reverse('categories:update', args=[category.pk]),
            {
                'name': 'Aluguel',
                'category_type': Category.CategoryType.EXPENSE,
                'color': '#F59E0B',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Categoria atualizada com sucesso.')],
        )
        category.refresh_from_db()
        self.assertEqual(category.name, 'Aluguel')
        self.assertEqual(
            category.category_type,
            Category.CategoryType.EXPENSE,
        )
        self.assertEqual(category.color, '#F59E0B')
        self.assertEqual(category.user, self.owner)

    def test_delete_page_asks_for_confirmation_without_deleting(self):
        category = create_category(self.owner)

        response = self.client.get(
            reverse('categories:delete', args=[category.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'categories/category_confirm_delete.html',
        )
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_delete_removes_category_and_redirects_with_message(self):
        category = create_category(self.owner)

        response = self.client.post(
            reverse('categories:delete', args=[category.pk])
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Categoria excluída com sucesso.')],
        )
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_success_message_is_displayed_on_list_page(self):
        category = create_category(self.owner)

        response = self.client.post(
            reverse('categories:delete', args=[category.pk]),
            follow=True,
        )

        self.assertContains(response, 'Categoria excluída com sucesso.')


class CategoryDuplicateTests(CategoryTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = create_category(cls.owner)

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_duplicate_shows_error_and_saves_nothing(self):
        response = self.client.post(
            self.create_url,
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.INCOME,
                'color': '#000000',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            None,
            DUPLICATE_MESSAGE,
        )
        self.assertContains(response, DUPLICATE_MESSAGE)
        self.assertEqual(Category.objects.filter(user=self.owner).count(), 1)

    def test_create_duplicate_ignores_surrounding_spaces(self):
        response = self.client.post(
            self.create_url,
            {
                'name': '  Salário  ',
                'category_type': Category.CategoryType.INCOME,
                'color': '#000000',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            None,
            DUPLICATE_MESSAGE,
        )
        self.assertEqual(Category.objects.filter(user=self.owner).count(), 1)

    def test_update_to_existing_name_and_type_shows_error(self):
        category = create_category(self.owner, name='Freelance')

        response = self.client.post(
            reverse('categories:update', args=[category.pk]),
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.INCOME,
                'color': '#000000',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            None,
            DUPLICATE_MESSAGE,
        )
        self.assertContains(response, DUPLICATE_MESSAGE)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Freelance')
        self.assertEqual(category.color, '#10B981')

    def test_create_same_name_with_other_type_is_allowed(self):
        response = self.client.post(
            self.create_url,
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.EXPENSE,
                'color': '#EF4444',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertEqual(
            Category.objects.filter(user=self.owner, name='Salário').count(),
            2,
        )

    def test_update_to_same_name_with_other_type_is_allowed(self):
        category = create_category(
            self.owner,
            name='Freelance',
            category_type=Category.CategoryType.EXPENSE,
        )

        response = self.client.post(
            reverse('categories:update', args=[category.pk]),
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.EXPENSE,
                'color': '#10B981',
            },
        )

        self.assertRedirects(response, self.list_url)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Salário')

    def test_create_same_name_and_type_of_other_user_is_allowed(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            self.create_url,
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.INCOME,
                'color': '#10B981',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertTrue(
            Category.objects.filter(
                user=self.other_user,
                name='Salário',
                category_type=Category.CategoryType.INCOME,
            ).exists()
        )

    def test_update_to_same_name_and_type_of_other_user_is_allowed(self):
        category = create_category(self.other_user, name='Freelance')
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse('categories:update', args=[category.pk]),
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.INCOME,
                'color': '#10B981',
            },
        )

        self.assertRedirects(response, self.list_url)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Salário')

    def test_update_own_category_keeping_name_and_type_is_allowed(self):
        response = self.client.post(
            reverse('categories:update', args=[self.category.pk]),
            {
                'name': 'Salário',
                'category_type': Category.CategoryType.INCOME,
                'color': '#3B82F6',
            },
        )

        self.assertRedirects(response, self.list_url)
        self.assertMessages(
            response,
            [Message(messages.SUCCESS, 'Categoria atualizada com sucesso.')],
        )
        self.category.refresh_from_db()
        self.assertEqual(self.category.color, '#3B82F6')

    def test_database_rejects_duplicate_for_same_user(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            create_category(self.owner)


class CategoryIsolationTests(CategoryTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = create_category(cls.owner, name='Categoria do dono')
        cls.update_url = reverse('categories:update', args=[cls.category.pk])
        cls.delete_url = reverse('categories:delete', args=[cls.category.pk])

    def setUp(self):
        self.client.force_login(self.other_user)

    def assert_category_unchanged(self):
        category = Category.objects.get(pk=self.category.pk)
        self.assertEqual(category.user, self.owner)
        self.assertEqual(category.name, 'Categoria do dono')
        self.assertEqual(category.category_type, Category.CategoryType.INCOME)
        self.assertEqual(category.color, '#10B981')

    def test_list_hides_categories_from_other_user(self):
        own_category = create_category(
            self.other_user,
            name='Categoria do outro',
        )

        response = self.client.get(self.list_url)

        self.assertEqual(list(response.context['categories']), [own_category])
        self.assertEqual(
            list(response.context['income_categories']),
            [own_category],
        )
        self.assertEqual(list(response.context['expense_categories']), [])
        self.assertContains(response, 'Categoria do outro')
        self.assertNotContains(response, 'Categoria do dono')
        self.assertNotContains(response, self.update_url)
        self.assertNotContains(response, self.delete_url)

    def test_get_update_returns_404(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 404)
        self.assert_category_unchanged()

    def test_post_update_returns_404_and_keeps_category(self):
        response = self.client.post(
            self.update_url,
            {
                'name': 'Categoria invadida',
                'category_type': Category.CategoryType.EXPENSE,
                'color': '#000000',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assert_category_unchanged()

    def test_get_delete_returns_404(self):
        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_category_unchanged()

    def test_post_delete_returns_404_and_keeps_category(self):
        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assert_category_unchanged()


class CategoryProtectedDeleteTests(CategoryTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.account = Account.objects.create(
            user=cls.owner,
            name='Conta corrente principal',
            initial_balance=Decimal('1000.00'),
        )
        cls.category = create_category(cls.owner)
        cls.transaction = Transaction.objects.create(
            user=cls.owner,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('100.00'),
            date=date(2026, 1, 15),
            description='Lançamento de teste',
            account=cls.account,
            category=cls.category,
        )
        cls.delete_url = reverse('categories:delete', args=[cls.category.pk])

    def setUp(self):
        self.client.force_login(self.owner)

    def test_post_delete_keeps_category_and_transaction(self):
        self.client.post(self.delete_url)

        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
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
        self.assertNotContains(response, 'Categoria excluída com sucesso.')

    def test_model_delete_raises_protected_error(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_category_can_be_deleted_after_removing_transactions(self):
        self.transaction.delete()

        response = self.client.post(self.delete_url)

        self.assertRedirects(response, self.list_url)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
