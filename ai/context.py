"""Immutable dataclass with the trusted data of an analysis run."""

from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.utils import timezone


@dataclass(frozen=True)
class AnalysisContext:
    user_id: int
    period_start: date
    period_end: date
    deadline: float
    owner_thread_id: int


def shift_month(month_start, months):
    """Return the first day of the month ``months`` away from month_start."""
    month_index = month_start.year * 12 + month_start.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def calculate_analysis_period():
    """Return (period_start, period_end) for the local date of today."""
    today = timezone.localdate()
    period_start = shift_month(
        today.replace(day=1),
        1 - settings.AI_ANALYSIS_WINDOW_MONTHS,
    )
    return period_start, today
