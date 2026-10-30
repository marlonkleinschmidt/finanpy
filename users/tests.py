from django.contrib.auth import authenticate
from django.test import TestCase

from users.forms import EmailAuthenticationForm, SignUpForm
from users.models import User

PASSWORD = 'SenhaForte!2026x'


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
