from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class FinancialAnalysis(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Em andamento'
        SUCCESS = 'success', 'Concluída'
        FAILED = 'failed', 'Falhou'

    class ErrorCode(models.TextChoices):
        AUTHENTICATION_ERROR = (
            'authentication_error',
            'Chave inválida ou revogada',
        )
        MODEL_UNAVAILABLE = 'model_unavailable', 'Modelo indisponível'
        RATE_LIMITED = 'rate_limited', 'Limite de uso ou cota esgotada'
        TIMEOUT = 'timeout', 'Tempo esgotado'
        PROVIDER_UNAVAILABLE = (
            'provider_unavailable',
            'Provedor indisponível',
        )
        LIMIT_EXCEEDED = 'limit_exceeded', 'Limite de chamadas atingido'
        INVALID_OUTPUT = 'invalid_output', 'Saída inválida'
        UNVERIFIED_OUTPUT = 'unverified_output', 'Evidências não conferidas'
        ABANDONED = 'abandoned', 'Execução interrompida'
        INTERNAL_ERROR = 'internal_error', 'Erro interno'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='financial_analyses',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    period_start = models.DateField('Início do período')
    period_end = models.DateField('Fim do período')
    generated_at = models.DateTimeField(
        'Gerada em',
        null=True,
        blank=True,
    )
    finished_at = models.DateTimeField(
        'Finalizada em',
        null=True,
        blank=True,
    )
    main_insight = models.JSONField('Insight principal', default=dict)
    insights = models.JSONField('Insights adicionais', default=list)
    recommendations = models.JSONField('Recomendações', default=list)
    alerts = models.JSONField('Alertas', default=list)
    data_limitations = models.JSONField(
        'Limitações dos dados',
        default=list,
    )
    metrics_snapshot = models.JSONField(
        'Totais do período',
        default=dict,
    )
    tool_calls = models.JSONField('Ferramentas chamadas', default=list)
    model_name = models.CharField('Modelo', max_length=100)
    prompt_version = models.CharField('Versão do prompt', max_length=20)
    input_tokens = models.PositiveIntegerField(
        'Tokens de entrada',
        default=0,
    )
    output_tokens = models.PositiveIntegerField(
        'Tokens de saída',
        default=0,
    )
    total_tokens = models.PositiveIntegerField(
        'Total de tokens',
        default=0,
    )
    duration_ms = models.PositiveIntegerField(
        'Duração (ms)',
        null=True,
        blank=True,
    )
    error_code = models.CharField(
        'Código de erro',
        max_length=30,
        blank=True,
        choices=ErrorCode.choices,
    )
    error_detail = models.CharField(
        'Detalhe do erro',
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Análise financeira'
        verbose_name_plural = 'Análises financeiras'
        indexes = [
            models.Index(
                fields=['user', 'status', '-generated_at'],
                name='ai_analysis_user_status_idx',
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='pending'),
                name='unique_pending_analysis_per_user',
            ),
        ]

    def __str__(self):
        return f'Análise {self.pk} ({self.get_status_display()})'
