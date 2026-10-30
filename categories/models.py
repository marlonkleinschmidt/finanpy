from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Entrada'
        EXPENSE = 'expense', 'Saída'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='categories',
    )
    name = models.CharField('Nome', max_length=100)
    category_type = models.CharField(
        'Tipo',
        max_length=20,
        choices=CategoryType.choices,
    )
    color = models.CharField('Cor', max_length=7, default='#8B5CF6')

    class Meta:
        ordering = ['category_type', 'name']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'category_type'],
                name='unique_category_per_user',
            ),
        ]

    def __str__(self):
        return self.name
