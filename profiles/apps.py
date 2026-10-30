from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    name = 'profiles'
    verbose_name = 'Perfis'

    def ready(self):
        from profiles import signals  # noqa: F401
