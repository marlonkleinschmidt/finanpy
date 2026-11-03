from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView

from ai.models import FinancialAnalysis
from ai.services import (
    GenerationOutcome,
    generate_analysis,
    get_stale_notice,
)
from core.mixins import UserQuerySetMixin

OUTCOME_MESSAGES = {
    GenerationOutcome.SUCCESS: (
        messages.SUCCESS,
        'Análise gerada com sucesso.',
    ),
    GenerationOutcome.FAILED: (
        messages.ERROR,
        'Não foi possível gerar a análise. Tente novamente mais tarde.',
    ),
    GenerationOutcome.ALREADY_RUNNING: (
        messages.ERROR,
        'Já existe uma análise em andamento.',
    ),
    GenerationOutcome.LIMIT_REACHED: (
        messages.ERROR,
        'Você atingiu o limite de análises de hoje.',
    ),
    GenerationOutcome.INSUFFICIENT_DATA: (
        messages.ERROR,
        'Ainda não há transações suficientes para gerar uma análise.',
    ),
    GenerationOutcome.DISABLED: (
        messages.ERROR,
        'O assistente não está disponível no momento.',
    ),
}


class AnalysisListView(LoginRequiredMixin, UserQuerySetMixin, ListView):
    model = FinancialAnalysis
    template_name = 'ai/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    # The primary key keeps the pages stable when created_at repeats.
    ordering = ['-created_at', '-pk']


class AnalysisDetailView(LoginRequiredMixin, UserQuerySetMixin, DetailView):
    model = FinancialAnalysis
    template_name = 'ai/analysis_detail.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stale_notice'] = get_stale_notice(self.object)
        return context


class AnalysisCreateView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # Do not wrap this call in transaction.atomic(): the service refuses
        # to run the agent inside a transaction (docs/ia.md).
        outcome = generate_analysis(request.user)
        level, text = OUTCOME_MESSAGES[outcome]
        messages.add_message(request, level, text)
        return redirect('dashboard')
