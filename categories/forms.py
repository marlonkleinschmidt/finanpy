from django import forms
from django.core.exceptions import ValidationError

from categories.models import Category
from core.forms import StyledFormMixin


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'category_type', 'color')
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # O rótulo padrão da opção vazia não tem tradução para pt-br.
        self.fields['category_type'].choices = [
            ('', 'Selecione o tipo'),
            *Category.CategoryType.choices,
        ]

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category_type = cleaned_data.get('category_type')
        if not name or not category_type:
            return cleaned_data

        # O campo user não está no form, então o ModelForm não valida a
        # UniqueConstraint e a duplicidade precisa ser checada aqui.
        duplicate_exists = (
            Category.objects.filter(
                user=self.user,
                name=name,
                category_type=category_type,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if duplicate_exists:
            raise ValidationError(
                'Você já possui uma categoria com este nome e tipo.'
            )
        return cleaned_data
