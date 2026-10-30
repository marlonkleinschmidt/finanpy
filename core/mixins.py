class UserQuerySetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class UserFormMixin:
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
