"""Analysis orchestration, limits, error handling and read functions.

Only entry point of the assistant for the rest of the system, and only module
that writes analyses. LangChain and OpenAI load inside the functions that run
the agent, never when Django starts (RNF23).
"""

import enum
import logging
import math
import threading
import time
import traceback
from datetime import datetime, timedelta

from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.models import Count, Max, Q
from django.utils import timezone

from ai.context import AnalysisContext, calculate_analysis_period
from ai.models import FinancialAnalysis
from ai.prompts import PROMPT_VERSION
from ai.queries import get_metrics_snapshot
from ai.validators import (
    extract_tool_calls,
    is_invalid_output,
    validate_output,
)

logger = logging.getLogger(__name__)

Status = FinancialAnalysis.Status
ErrorCode = FinancialAnalysis.ErrorCode

ERROR_DETAIL_MAX_LENGTH = 255


class GenerationOutcome(enum.StrEnum):
    SUCCESS = 'success'
    FAILED = 'failed'
    ALREADY_RUNNING = 'already_running'
    LIMIT_REACHED = 'limit_reached'
    INSUFFICIENT_DATA = 'insufficient_data'
    DISABLED = 'disabled'


class AnalysisState(enum.StrEnum):
    """States the server decides. Loading exists only in the browser."""

    WITH_ANALYSIS = 'with_analysis'
    NO_ANALYSIS = 'no_analysis'
    RUNNING = 'running'
    FAILED = 'failed'
    STALE = 'stale'
    LIMIT_REACHED = 'limit_reached'
    INSUFFICIENT_DATA = 'insufficient_data'
    DISABLED = 'disabled'


def _pending_cutoff():
    minutes = settings.AI_ANALYSIS_PENDING_TIMEOUT_MINUTES
    return timezone.now() - timedelta(minutes=minutes)


def _local_day_bounds():
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    return (
        timezone.make_aware(datetime.combine(today, datetime.min.time())),
        timezone.make_aware(datetime.combine(tomorrow, datetime.min.time())),
    )


def _transaction_count(snapshot):
    return snapshot['income_count'] + snapshot['expense_count']


def _close_abandoned_analyses(user_id):
    now = timezone.now()
    FinancialAnalysis.objects.filter(
        user_id=user_id,
        status=Status.PENDING,
        created_at__lt=_pending_cutoff(),
    ).update(
        status=Status.FAILED,
        error_code=ErrorCode.ABANDONED,
        finished_at=now,
        updated_at=now,
    )


def _is_daily_limit_reached(user_id):
    start, end = _local_day_bounds()
    created_today = FinancialAnalysis.objects.filter(
        user_id=user_id,
        created_at__gte=start,
        created_at__lt=end,
    ).count()
    return created_today >= settings.AI_ANALYSIS_DAILY_LIMIT


def _create_pending_analysis(user_id, period_start, period_end, snapshot):
    """Return the new record, or None if the user already has one pending."""
    try:
        with transaction.atomic():
            return FinancialAnalysis.objects.create(
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
                metrics_snapshot=snapshot,
                model_name=settings.AI_MODEL_NAME,
                prompt_version=PROMPT_VERSION,
            )
    except IntegrityError:
        return None


def _error_code_for_exception(error):
    try:
        import openai
        from langchain.agents.structured_output import (
            MultipleStructuredOutputsError,
            StructuredOutputValidationError,
        )
        from langgraph.errors import GraphRecursionError
    except ImportError:
        return ErrorCode.INTERNAL_ERROR

    # APITimeoutError is a subclass of APIConnectionError, so it comes first.
    error_codes = (
        (
            (openai.AuthenticationError, openai.PermissionDeniedError),
            ErrorCode.AUTHENTICATION_ERROR,
        ),
        (openai.NotFoundError, ErrorCode.MODEL_UNAVAILABLE),
        (openai.RateLimitError, ErrorCode.RATE_LIMITED),
        (openai.APITimeoutError, ErrorCode.TIMEOUT),
        (
            (openai.APIConnectionError, openai.InternalServerError),
            ErrorCode.PROVIDER_UNAVAILABLE,
        ),
        (GraphRecursionError, ErrorCode.LIMIT_EXCEEDED),
        (
            (StructuredOutputValidationError, MultipleStructuredOutputsError),
            ErrorCode.INVALID_OUTPUT,
        ),
    )
    for error_classes, error_code in error_codes:
        if isinstance(error, error_classes):
            return error_code
    return ErrorCode.INTERNAL_ERROR


def _log_exception(analysis_id, error_code, error):
    # logger.exception would print the message and the chained exceptions,
    # which may hold the API key or descriptions (docs/ia.md). format_tb
    # prints only files and lines of source code.
    logger.error(
        'Analysis %s failed: error_code=%s exception=%s\n%s',
        analysis_id,
        error_code,
        type(error).__name__,
        ''.join(traceback.format_tb(error.__traceback__)),
    )


def _failure_fields(error_code, error_detail=''):
    return {
        'status': Status.FAILED,
        'error_code': error_code,
        'error_detail': error_detail[:ERROR_DETAIL_MAX_LENGTH],
    }


def _code_for_missing_output(messages, context):
    if time.monotonic() >= context.deadline:
        return ErrorCode.TIMEOUT
    if is_invalid_output(messages, settings.AI_MAX_MODEL_CALLS):
        return ErrorCode.INVALID_OUTPUT
    return ErrorCode.LIMIT_EXCEEDED


def _fields_from_run(run, context):
    if run.structured_response is None:
        return _failure_fields(
            _code_for_missing_output(run.messages, context)
        )
    check = validate_output(
        run.structured_response.model_dump(mode='json'),
        run.messages,
    )
    if not check.is_verified:
        return _failure_fields(ErrorCode.UNVERIFIED_OUTPUT)
    return {
        'status': Status.SUCCESS,
        'generated_at': timezone.now(),
        **check.content,
    }


def _ensure_no_open_transaction():
    # An open transaction would block the writes of SQLite during the model
    # call, and the tools, in other threads, would not see its data.
    if connection.in_atomic_block:
        raise RuntimeError('The agent cannot run inside a transaction.')


def _usage_fields(tracker):
    if tracker is None:
        return {}
    return {
        **tracker.token_totals(),
        'tool_calls': extract_tool_calls(tracker.ai_messages),
    }


def _finish_analysis(analysis_id, fields):
    """Write the end of a run, only over the same pending record.

    No row is updated if the user was deleted during the run, or if the
    record was closed as abandoned, which must not change anymore (RN07).
    """
    now = timezone.now()
    return FinancialAnalysis.objects.filter(
        pk=analysis_id,
        status=Status.PENDING,
    ).update(finished_at=now, updated_at=now, **fields)


def _run_and_record(analysis):
    started_at = time.monotonic()
    tracker = None
    try:
        _ensure_no_open_transaction()
        from ai.agent import RunTracker, run_agent

        tracker = RunTracker()
        context = AnalysisContext(
            user_id=analysis.user_id,
            period_start=analysis.period_start,
            period_end=analysis.period_end,
            deadline=time.monotonic() + settings.AI_RUN_BUDGET_SECONDS,
            owner_thread_id=threading.get_ident(),
        )
        run = run_agent(context, tracker=tracker)
        fields = _fields_from_run(run, context)
    except Exception as error:
        error_code = _error_code_for_exception(error)
        _log_exception(analysis.pk, error_code, error)
        fields = _failure_fields(error_code, type(error).__name__)

    fields.update(_usage_fields(tracker))
    fields['duration_ms'] = int((time.monotonic() - started_at) * 1000)
    updated = _finish_analysis(analysis.pk, fields)
    if updated and fields['status'] == Status.SUCCESS:
        return GenerationOutcome.SUCCESS
    return GenerationOutcome.FAILED


def _generate_analysis(user_id):
    _close_abandoned_analyses(user_id)
    if not settings.OPENAI_API_KEY:
        return GenerationOutcome.DISABLED

    period_start, period_end = calculate_analysis_period()
    snapshot = get_metrics_snapshot(user_id, period_start, period_end)
    if _transaction_count(snapshot) < settings.AI_ANALYSIS_MIN_TRANSACTIONS:
        return GenerationOutcome.INSUFFICIENT_DATA
    if _is_daily_limit_reached(user_id):
        return GenerationOutcome.LIMIT_REACHED

    analysis = _create_pending_analysis(
        user_id,
        period_start,
        period_end,
        snapshot,
    )
    if analysis is None:
        return GenerationOutcome.ALREADY_RUNNING
    return _run_and_record(analysis)


def generate_analysis(user):
    """Run the flow of PRD 14.13 and return a GenerationOutcome.

    Never raises an Exception. If the final write fails, the record stays
    pending and the first step of a later call closes it.
    """
    try:
        return _generate_analysis(user.pk)
    except Exception as error:
        _log_exception(None, ErrorCode.INTERNAL_ERROR, error)
        return GenerationOutcome.FAILED


def get_latest_valid_analysis(user):
    """Return the last successful analysis of the user, or None. One query."""
    return (
        FinancialAnalysis.objects.filter(
            user_id=user.pk,
            status=Status.SUCCESS,
        )
        .order_by('-generated_at', '-pk')
        .first()
    )


def _is_stale(analysis):
    limit = timedelta(days=settings.AI_ANALYSIS_STALE_DAYS)
    return timezone.now() - analysis.generated_at > limit


def _analysis_stats(user_id):
    start, end = _local_day_bounds()
    return FinancialAnalysis.objects.filter(user_id=user_id).aggregate(
        created_today=Count(
            'pk',
            filter=Q(created_at__gte=start, created_at__lt=end),
        ),
        running=Count(
            'pk',
            filter=Q(
                status=Status.PENDING,
                created_at__gte=_pending_cutoff(),
            ),
        ),
        latest_failure=Max('created_at', filter=Q(status=Status.FAILED)),
    )


def _decide_state(user_id, analysis, is_stale):
    """Same order of generate_analysis, then what happened to the last run."""
    if not settings.OPENAI_API_KEY:
        return AnalysisState.DISABLED

    stats = _analysis_stats(user_id)
    if stats['running']:
        return AnalysisState.RUNNING

    period_start, period_end = calculate_analysis_period()
    snapshot = get_metrics_snapshot(user_id, period_start, period_end)
    if _transaction_count(snapshot) < settings.AI_ANALYSIS_MIN_TRANSACTIONS:
        return AnalysisState.INSUFFICIENT_DATA
    if stats['created_today'] >= settings.AI_ANALYSIS_DAILY_LIMIT:
        return AnalysisState.LIMIT_REACHED

    latest_failure = stats['latest_failure']
    if latest_failure and (
        analysis is None or latest_failure > analysis.created_at
    ):
        return AnalysisState.FAILED
    if is_stale:
        return AnalysisState.STALE
    if analysis is None:
        return AnalysisState.NO_ANALYSIS
    return AnalysisState.WITH_ANALYSIS


def _state_notice(state):
    return {
        AnalysisState.NO_ANALYSIS: (
            'Você ainda não tem análises. Gere a primeira para receber dicas '
            'sobre suas finanças.'
        ),
        AnalysisState.RUNNING: (
            'Há uma análise em andamento. Atualize a página em instantes.'
        ),
        AnalysisState.FAILED: 'Não foi possível concluir a última análise.',
        AnalysisState.LIMIT_REACHED: (
            'Você atingiu o limite de análises de hoje. Tente novamente '
            'amanhã.'
        ),
        AnalysisState.INSUFFICIENT_DATA: (
            'Registre pelo menos '
            f'{settings.AI_ANALYSIS_MIN_TRANSACTIONS} transações para gerar '
            'uma análise.'
        ),
        AnalysisState.DISABLED: (
            'O assistente não está disponível no momento.'
        ),
    }.get(state)


def _stale_notice(can_generate=True):
    days = settings.AI_ANALYSIS_STALE_DAYS
    notice = f'Esta análise tem mais de {days} dias.'
    if can_generate:
        return f'{notice} Gere uma nova para refletir seus dados atuais.'
    return notice


def get_stale_notice(analysis):
    """Return the RN06 notice of an analysis, or None. No queries."""
    if analysis.status == Status.SUCCESS and _is_stale(analysis):
        return _stale_notice()
    return None


def get_dashboard_analysis_state(user):
    """Return the data of the dashboard card. At most 3 queries, no writes.

    analysis is the last valid one, kept whatever the state is (RN05). A
    stale analysis keeps its notice, even if another state comes first.
    """
    analysis = get_latest_valid_analysis(user)
    is_stale = analysis is not None and _is_stale(analysis)
    state = _decide_state(user.pk, analysis, is_stale)
    can_generate = state in (
        AnalysisState.WITH_ANALYSIS,
        AnalysisState.NO_ANALYSIS,
        AnalysisState.FAILED,
        AnalysisState.STALE,
    )

    notices = []
    notice = _state_notice(state)
    if notice:
        notices.append(notice)
    if is_stale:
        notices.append(_stale_notice(can_generate))

    minutes = math.ceil(settings.AI_RUN_BUDGET_SECONDS / 60)
    return {
        'state': state,
        'analysis': analysis,
        'is_stale': is_stale,
        'notices': notices,
        'can_generate': can_generate,
        'loading_message': (
            f'Gerando análise... isso pode levar até {minutes} minutos.'
        ),
    }
