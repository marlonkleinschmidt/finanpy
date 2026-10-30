from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from categories.forms import CategoryForm
from categories.models import Category
from core.mixins import UserFormMixin, UserQuerySetMixin


class CategoryFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class CategoryListView(LoginRequiredMixin, UserQuerySetMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['income_categories'] = self.object_list.filter(
            category_type=Category.CategoryType.INCOME
        )
        context['expense_categories'] = self.object_list.filter(
            category_type=Category.CategoryType.EXPENSE
        )
        return context


class CategoryCreateView(
    LoginRequiredMixin,
    UserFormMixin,
    CategoryFormKwargsMixin,
    SuccessMessageMixin,
    CreateView,
):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('categories:list')
    success_message = 'Categoria criada com sucesso.'


class CategoryUpdateView(
    LoginRequiredMixin,
    UserQuerySetMixin,
    CategoryFormKwargsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('categories:list')
    success_message = 'Categoria atualizada com sucesso.'


class CategoryDeleteView(
    LoginRequiredMixin, UserQuerySetMixin, SuccessMessageMixin, DeleteView
):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('categories:list')
    success_message = 'Categoria excluída com sucesso.'

    def form_valid(self, form):
        # O erro sai de super() antes de o SuccessMessageMixin registrar a
        # mensagem de sucesso, então só a mensagem de erro é exibida.
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                'Esta categoria possui transações e não pode ser excluída.',
            )
            return redirect(self.success_url)
