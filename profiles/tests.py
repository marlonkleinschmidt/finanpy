from django.contrib.auth import get_user_model
from django.contrib.messages import SUCCESS
from django.contrib.messages.storage.base import Message
from django.contrib.messages.test import MessagesTestMixin
from django.test import TestCase
from django.urls import reverse

from profiles.models import Profile

User = get_user_model()

SUCCESS_MESSAGE = 'Perfil atualizado com sucesso.'


class ProfileSignalTests(TestCase):
    def test_creating_user_creates_profile(self):
        user = User.objects.create_user(
            email='ana@finanpy.test',
            password='SenhaForte!123',
        )

        profile = Profile.objects.get(user=user)
        self.assertEqual(user.profile, profile)
        self.assertEqual(profile.phone, '')

    def test_saving_existing_user_does_not_create_second_profile(self):
        user = User.objects.create_user(
            email='ana@finanpy.test',
            password='SenhaForte!123',
        )
        original_profile_pk = user.profile.pk

        user.first_name = 'Ana'
        user.save()

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.pk, original_profile_pk)
        self.assertEqual(Profile.objects.count(), 1)


class ProfileUpdateViewTests(MessagesTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='ana@finanpy.test',
            password='SenhaForte!123',
            first_name='Ana',
            last_name='Souza',
        )
        cls.user.profile.phone = '11 90000-0000'
        cls.user.profile.save()
        cls.url = reverse('profile')

    def assert_nothing_changed(self):
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.first_name, 'Ana')
        self.assertEqual(user.last_name, 'Souza')
        self.assertEqual(user.profile.phone, '11 90000-0000')

    def test_anonymous_get_redirects_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={self.url}',
        )

    def test_anonymous_post_redirects_to_login_without_changes(self):
        response = self.client.post(
            self.url,
            {
                'first_name': 'Beatriz',
                'last_name': 'Lima',
                'phone': '21 98888-7777',
            },
        )

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={self.url}',
        )
        self.assert_nothing_changed()

    def test_valid_post_updates_profile_and_user(self):
        self.client.force_login(self.user)

        self.client.post(
            self.url,
            {
                'first_name': 'Beatriz',
                'last_name': 'Lima',
                'phone': '21 98888-7777',
            },
        )

        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.first_name, 'Beatriz')
        self.assertEqual(user.last_name, 'Lima')
        self.assertEqual(user.profile.phone, '21 98888-7777')

    def test_valid_post_redirects_and_shows_success_message(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                'first_name': 'Beatriz',
                'last_name': 'Lima',
                'phone': '21 98888-7777',
            },
        )

        self.assertRedirects(response, self.url)
        self.assertMessages(response, [Message(SUCCESS, SUCCESS_MESSAGE)])

    def test_post_with_empty_first_name_saves_nothing(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                'first_name': '',
                'last_name': 'Lima',
                'phone': '21 98888-7777',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('first_name', response.context['user_form'].errors)
        self.assertMessages(response, [])
        self.assert_nothing_changed()

    def test_post_with_too_long_phone_saves_nothing(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                'first_name': 'Beatriz',
                'last_name': 'Lima',
                'phone': '1' * 21,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('phone', response.context['form'].errors)
        self.assertMessages(response, [])
        self.assert_nothing_changed()
