from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Sum
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import UserFormMixin, UserQuerySetMixin
from transactions.forms import TransactionFilterForm, TransactionForm
from transactions.models import Transaction

FILTER_LOOKUPS = {
    'start_date': 'date__gte',
    'end_date': 'date__lte',
    'transaction_type': 'transaction_type',
    'account': 'account',
    'category': 'category',
}


class TransactionFormViewMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_accounts'] = self.request.user.accounts.exists()
        context['has_categories'] = self.request.user.categories.exists()
        return context


class TransactionListView(LoginRequiredMixin, UserQuerySetMixin, ListView):
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    @cached_property
    def filter_form(self):
        return TransactionFilterForm(
            self.request.GET, user=self.request.user
        )

    def get_queryset(self):
        queryset = (
            super().get_queryset().select_related('account', 'category')
        )
        # Com filtro inválido a lista fica completa e o form exibe os erros.
        if not self.filter_form.is_valid():
            return queryset

        cleaned_data = self.filter_form.cleaned_data
        filters = {
            lookup: cleaned_data[name]
            for name, lookup in FILTER_LOOKUPS.items()
            if cleaned_data[name]
        }
        return queryset.filter(**filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # object_list é o resultado filtrado completo, não a página atual.
        totals = self.object_list.aggregate(
            income=Sum(
                'amount',
                filter=Q(transaction_type=Transaction.TransactionType.INCOME),
            ),
            expense=Sum(
                'amount',
                filter=Q(transaction_type=Transaction.TransactionType.EXPENSE),
            ),
        )
        # No SQLite o Sum volta com 15 dígitos significativos, sem arredondar
        # para as casas decimais do campo.
        total_income = totals['income'] or Decimal('0')
        total_expense = totals['expense'] or Decimal('0')
        context['filter_form'] = self.filter_form
        context['total_income'] = total_income.quantize(Decimal('0.01'))
        context['total_expense'] = total_expense.quantize(Decimal('0.01'))
        context['has_filters'] = self.filter_form.is_valid() and any(
            self.filter_form.cleaned_data.values()
        )
        return context


class TransactionCreateView(
    LoginRequiredMixin,
    UserFormMixin,
    TransactionFormViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('transactions:list')
    success_message = 'Transação registrada com sucesso.'


class TransactionUpdateView(
    LoginRequiredMixin,
    UserQuerySetMixin,
    TransactionFormViewMixin,
    SuccessMessageMixin,
    UpdateView,
):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('transactions:list')
    success_message = 'Transação atualizada com sucesso.'


class TransactionDeleteView(
    LoginRequiredMixin, UserQuerySetMixin, SuccessMessageMixin, DeleteView
):
    model = Transaction
    template_name = 'transactions/transaction_confirm_delete.html'
    context_object_name = 'transaction'
    success_url = reverse_lazy('transactions:list')
    success_message = 'Transação excluída com sucesso.'
