from django import forms

from accounts.models import Account
from categories.models import Category
from core.forms import StyledFormMixin
from transactions.models import Transaction

CATEGORY_GROUPS = (
    ('Entradas', Category.CategoryType.INCOME),
    ('Saídas', Category.CategoryType.EXPENSE),
)


def build_date_widget():
    # O input type=date exige o valor em ISO, mesmo com pt-br ativo.
    return forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


def build_category_choices(categories, empty_label):
    choices = [('', empty_label)]
    for group_label, category_type in CATEGORY_GROUPS:
        options = [
            (category.pk, category.name)
            for category in categories
            if category.category_type == category_type
        ]
        if options:
            choices.append((group_label, options))
    return choices


class TransactionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            'transaction_type',
            'amount',
            'date',
            'description',
            'account',
            'category',
        )
        widgets = {
            'date': build_date_widget(),
        }
        error_messages = {
            'amount': {'min_value': 'O valor deve ser maior que zero.'},
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # O rótulo padrão da opção vazia não tem tradução para pt-br.
        self.fields['transaction_type'].choices = [
            ('', 'Selecione o tipo'),
            *Transaction.TransactionType.choices,
        ]
        self.fields['account'].empty_label = 'Selecione a conta'
        self.fields['account'].queryset = Account.objects.filter(user=user)

        # Atribuir queryset reseta widget.choices, então os grupos só podem
        # ser montados depois. A validação continua pelo queryset.
        category_field = self.fields['category']
        category_field.queryset = Category.objects.filter(user=user)
        category_field.choices = build_category_choices(
            category_field.queryset, 'Selecione a categoria'
        )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        transaction_type = cleaned_data.get('transaction_type')
        if not category or not transaction_type:
            return cleaned_data

        if category.category_type != transaction_type:
            self.add_error(
                'category',
                'A categoria deve ser do mesmo tipo da transação.',
            )
        return cleaned_data


class TransactionFilterForm(StyledFormMixin, forms.Form):
    start_date = forms.DateField(
        label='Data inicial',
        required=False,
        widget=build_date_widget(),
    )
    end_date = forms.DateField(
        label='Data final',
        required=False,
        widget=build_date_widget(),
    )
    transaction_type = forms.ChoiceField(
        label='Tipo',
        required=False,
        choices=[
            ('', 'Todos os tipos'),
            *Transaction.TransactionType.choices,
        ],
    )
    account = forms.ModelChoiceField(
        label='Conta',
        required=False,
        queryset=Account.objects.none(),
        empty_label='Todas as contas',
    )
    category = forms.ModelChoiceField(
        label='Categoria',
        required=False,
        queryset=Category.objects.none(),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(user=user)

        # Mesma ordem do TransactionForm: queryset primeiro, grupos depois.
        category_field = self.fields['category']
        category_field.queryset = Category.objects.filter(user=user)
        category_field.choices = build_category_choices(
            category_field.queryset, 'Todas as categorias'
        )
