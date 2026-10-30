from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum

from core.models import TimeStampedModel


class Account(TimeStampedModel):
    class AccountType(models.TextChoices):
        CHECKING = 'checking', 'Conta corrente'
        SAVINGS = 'savings', 'Poupança'
        WALLET = 'wallet', 'Carteira'
        INVESTMENT = 'investment', 'Investimento'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='accounts',
    )
    name = models.CharField('Nome', max_length=100)
    bank_name = models.CharField('Banco', max_length=100, blank=True)
    account_type = models.CharField(
        'Tipo',
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CHECKING,
    )
    initial_balance = models.DecimalField(
        'Saldo inicial',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'

    def __str__(self):
        return self.name

    @property
    def current_balance(self):
        # Os tipos ficam como texto para evitar import circular com
        # transactions.models.
        totals = self.transactions.aggregate(
            income=Sum('amount', filter=Q(transaction_type='income')),
            expense=Sum('amount', filter=Q(transaction_type='expense')),
        )
        income = totals['income'] or Decimal('0')
        expense = totals['expense'] or Decimal('0')
        # No SQLite o Sum volta com 15 dígitos significativos, sem arredondar
        # para as casas decimais do campo.
        balance = self.initial_balance + income - expense
        return balance.quantize(Decimal('0.01'))
