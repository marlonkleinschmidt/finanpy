from django.contrib.auth import authenticate, get_user
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from users.forms import EmailAuthenticationForm, SignUpForm
from users.models import User

PASSWORD = 'SenhaForte!2026x'
INVALID_LOGIN_MESSAGE = 'E-mail ou senha inválidos.'
DUPLICATE_EMAIL_MESSAGE = 'Já existe um usuário com este e-mail.'


def create_user(email='ana@example.com'):
    return User.objects.create_user(
        email,
        PASSWORD,
        first_name='Ana',
        last_name='Costa',
    )


def signup_data(email='ana@example.com', **overrides):
    return {
        'first_name': 'Ana',
        'last_name': 'Costa',
        'email': email,
        'password1': PASSWORD,
        'password2': PASSWORD,
        **overrides,
    }


class CreateUserTests(TestCase):
    def test_create_user_normalizes_email(self):
        user = create_user('Ana@Example.COM')

        self.assertEqual(user.email, 'ana@example.com')

    def test_create_user_hashes_password(self):
        user = create_user()

        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.check_password('senha-errada'))

    def test_create_user_has_no_admin_flags(self):
        user = create_user()

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, 'O e-mail é obrigatório.'):
            User.objects.create_user('', PASSWORD)


class CreateSuperuserTests(TestCase):
    def test_create_superuser_sets_admin_flags(self):
        user = User.objects.create_superuser(
            'Admin@Example.COM',
            PASSWORD,
            first_name='Admin',
            last_name='Teste',
        )

        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class DuplicateEmailTests(TestCase):
    def setUp(self):
        create_user()

    def test_model_rejects_duplicate_email(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            create_user()

        self.assertEqual(User.objects.count(), 1)

    def test_model_rejects_email_differing_only_by_case(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            create_user('ANA@example.com')

        self.assertEqual(User.objects.count(), 1)

    def test_signup_form_rejects_duplicate_email(self):
        form = SignUpForm(data=signup_data())

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], [DUPLICATE_EMAIL_MESSAGE])

    def test_signup_view_rejects_duplicate_email(self):
        response = self.client.post(reverse('signup'), signup_data())

        self.assertContains(response, DUPLICATE_EMAIL_MESSAGE)
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(get_user(self.client).is_authenticated)


class SignUpViewTests(TestCase):
    def test_get_renders_signup_form(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_post_creates_user(self):
        self.client.post(reverse('signup'), signup_data('Ana@Example.COM'))

        user = User.objects.get()
        self.assertEqual(user.email, 'ana@example.com')
        self.assertEqual(user.first_name, 'Ana')
        self.assertEqual(user.last_name, 'Costa')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_post_authenticates_new_user(self):
        self.client.post(reverse('signup'), signup_data())

        self.assertEqual(get_user(self.client), User.objects.get())

    def test_post_redirects_to_dashboard(self):
        response = self.client.post(reverse('signup'), signup_data())

        self.assertRedirects(response, reverse('dashboard'))

    def test_post_with_mismatched_passwords_does_not_create_user(self):
        response = self.client.post(
            reverse('signup'),
            signup_data(password2='OutraSenha!2026y'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context['form'].errors)
        self.assertFalse(User.objects.exists())
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_authenticated_user_is_redirected_to_dashboard(self):
        self.client.force_login(create_user())

        response = self.client.get(reverse('signup'))

        self.assertRedirects(response, reverse('dashboard'))


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def login(self, email, password):
        return self.client.post(
            reverse('login'),
            {'username': email, 'password': password},
        )

    def test_correct_credentials_authenticate_user(self):
        self.login('ana@example.com', PASSWORD)

        self.assertEqual(get_user(self.client), self.user)

    def test_correct_credentials_redirect_to_dashboard(self):
        response = self.login('ana@example.com', PASSWORD)

        self.assertRedirects(response, reverse('dashboard'))

    def test_wrong_password_shows_error_and_does_not_authenticate(self):
        response = self.login('ana@example.com', 'senha-errada')

        self.assertContains(response, INVALID_LOGIN_MESSAGE)
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_unknown_email_shows_error_and_does_not_authenticate(self):
        response = self.login('outra@example.com', PASSWORD)

        self.assertContains(response, INVALID_LOGIN_MESSAGE)
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_authenticated_user_is_redirected_to_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('login'))

        self.assertRedirects(response, reverse('dashboard'))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_post_redirects_to_home(self):
        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'))

    def test_post_ends_session(self):
        self.client.post(reverse('logout'))

        self.assertFalse(get_user(self.client).is_authenticated)

    def test_dashboard_requires_login_after_logout(self):
        self.client.post(reverse('logout'))

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("dashboard")}',
        )

    def test_get_is_not_allowed_and_keeps_session(self):
        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(get_user(self.client), self.user)


class EmailCaseInsensitiveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'Maria@Example.COM',
            PASSWORD,
            first_name='Maria',
            last_name='Silva',
        )

    def signup_form(self, email):
        return SignUpForm(
            data={
                'first_name': 'Maria',
                'last_name': 'Souza',
                'email': email,
                'password1': PASSWORD,
                'password2': PASSWORD,
            }
        )

    def test_create_user_stores_lowercase_email(self):
        self.assertEqual(self.user.email, 'maria@example.com')

    def test_signup_stores_lowercase_email(self):
        form = self.signup_form('Joana@Example.COM')

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().email, 'joana@example.com')

    def test_signup_rejects_email_differing_only_by_case(self):
        form = self.signup_form('MARIA@example.com')

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['email'],
            ['Já existe um usuário com este e-mail.'],
        )
        self.assertEqual(User.objects.count(), 1)

    def test_authenticate_ignores_email_case(self):
        user = authenticate(username='MARIA@EXAMPLE.COM', password=PASSWORD)

        self.assertEqual(user, self.user)

    def test_login_form_ignores_email_case(self):
        form = EmailAuthenticationForm(
            data={'username': 'MARIA@EXAMPLE.COM', 'password': PASSWORD}
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_admin_add_rejects_email_differing_only_by_case(self):
        admin = User.objects.create_superuser(
            'admin@example.com',
            PASSWORD,
            first_name='Admin',
            last_name='Teste',
        )
        self.client.force_login(admin)

        response = self.client.post(
            '/admin/users/user/add/',
            {
                'email': 'MARIA@example.com',
                'first_name': 'Maria',
                'last_name': 'Souza',
                'usable_password': 'true',
                'password1': PASSWORD,
                'password2': PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 2)
