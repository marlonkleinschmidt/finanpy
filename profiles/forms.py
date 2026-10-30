from django import forms

from core.forms import StyledFormMixin
from profiles.models import Profile
from users.models import User


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone',)
        labels = {
            'phone': 'Telefone',
        }
