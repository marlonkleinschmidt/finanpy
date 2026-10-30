from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.forms import AccountForm
from accounts.models import Account
from core.mixins import UserFormMixin, UserQuerySetMixin


class AccountListView(LoginRequiredMixin, UserQuerySetMixin, ListView):
    model = Account
    template_name = 'accounts/account_list.html'
    context_object_name = 'accounts'


class AccountCreateView(
    LoginRequiredMixin, UserFormMixin, SuccessMessageMixin, CreateView
):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:list')
    success_message = 'Conta criada com sucesso.'


class AccountUpdateView(
    LoginRequiredMixin, UserQuerySetMixin, SuccessMessageMixin, UpdateView
):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:list')
    success_message = 'Conta atualizada com sucesso.'


class AccountDeleteView(
    LoginRequiredMixin, UserQuerySetMixin, SuccessMessageMixin, DeleteView
):
    model = Account
    template_name = 'accounts/account_confirm_delete.html'
    context_object_name = 'account'
    success_url = reverse_lazy('accounts:list')
    success_message = 'Conta excluída com sucesso.'

    def form_valid(self, form):
        # O erro sai de super() antes de o SuccessMessageMixin registrar a
        # mensagem de sucesso, então só a mensagem de erro é exibida.
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                'Esta conta possui transações e não pode ser excluída.',
            )
            return redirect(self.success_url)
