from django import forms

# As classes ficam escritas por inteiro porque o Tailwind lê este arquivo
# como texto e não reconhece nomes montados em tempo de execução.
INPUT_CLASSES = (
    'w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 '
    'text-slate-100 placeholder-slate-500 focus:border-violet-500 '
    'focus:ring-2 focus:ring-violet-500/40 focus:outline-none '
    'aria-invalid:border-rose-500 aria-invalid:focus:ring-rose-500/40'
)
CHECKBOX_CLASSES = (
    'size-4 rounded border border-slate-700 bg-slate-800 '
    'accent-violet-500 focus:ring-2 focus:ring-violet-500/40 '
    'focus:outline-none aria-invalid:border-rose-500 '
    'aria-invalid:focus:ring-rose-500/40'
)
COLOR_INPUT_CLASSES = (
    'h-11 w-20 cursor-pointer rounded-xl bg-slate-800 border '
    'border-slate-700 p-1 focus:border-violet-500 focus:ring-2 '
    'focus:ring-violet-500/40 focus:outline-none '
    'aria-invalid:border-rose-500 aria-invalid:focus:ring-rose-500/40'
)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            classes = self._get_widget_classes(widget)
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {classes}'.strip()

    @staticmethod
    def _get_widget_classes(widget):
        if isinstance(widget, forms.CheckboxInput):
            return CHECKBOX_CLASSES
        # Nem todo widget tem input_type: Textarea, por exemplo, não tem.
        if getattr(widget, 'input_type', None) == 'color':
            return COLOR_INPUT_CLASSES
        return INPUT_CLASSES
