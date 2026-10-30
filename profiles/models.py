from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Profile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone = models.CharField('Telefone', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.user}'
