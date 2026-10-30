from django import forms

from accounts.models import Account
from core.forms import StyledFormMixin


class AccountForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Account
        fields = ('name', 'bank_name', 'account_type', 'initial_balance')
