from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class Transaction(TimeStampedModel):
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Entrada'
        EXPENSE = 'expense', 'Saída'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    transaction_type = models.CharField(
        'Tipo',
        max_length=20,
        choices=TransactionType.choices,
    )
    amount = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    date = models.DateField('Data', default=timezone.localdate)
    description = models.CharField('Descrição', max_length=255)
    account = models.ForeignKey(
        'accounts.Account',
        verbose_name='Conta',
        on_delete=models.PROTECT,
        related_name='transactions',
    )
    category = models.ForeignKey(
        'categories.Category',
        verbose_name='Categoria',
        on_delete=models.PROTECT,
        related_name='transactions',
    )

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'

    def __str__(self):
        return self.description
