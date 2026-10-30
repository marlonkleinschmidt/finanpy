from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import UpdateView

from profiles.forms import ProfileForm, UserUpdateForm


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profile')
    success_message = 'Perfil atualizado com sucesso.'

    def get_object(self, queryset=None):
        return self.request.user.profile

    @cached_property
    def user_form(self):
        # A validação de um ModelForm altera a instância em memória. Com uma
        # cópia do banco, um nome inválido não chega ao request.user, que é
        # o que a sidebar exibe.
        user = get_user_model().objects.get(pk=self.request.user.pk)
        data = self.request.POST if self.request.method == 'POST' else None
        return UserUpdateForm(data, instance=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = self.user_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        # A lista garante que os dois forms sejam validados, sem
        # curto-circuito.
        if all([form.is_valid(), self.user_form.is_valid()]):
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            self.user_form.save()
            return super().form_valid(form)
