from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    UsernameField,
)

from core.forms import StyledFormMixin
from users.models import User


class SignUpForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
        }
        error_messages = {
            'email': {
                'unique': 'Já existe um usuário com este e-mail.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmação de senha'


class EmailAuthenticationForm(StyledFormMixin, AuthenticationForm):
    username = UsernameField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'E-mail ou senha inválidos.',
    }
