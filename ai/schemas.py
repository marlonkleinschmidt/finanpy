"""Pydantic schemas of the agent's structured output."""

from typing import Literal

from pydantic import BaseModel, Field

SourceTool = Literal[
    'get_financial_summary',
    'get_monthly_evolution',
    'get_category_breakdown',
    'get_category_changes',
    'get_recurring_expenses',
    'get_largest_transactions',
    'get_accounts_overview',
]


class EvidenceItem(BaseModel):
    """A value copied exactly as a tool returned it."""

    label: str = Field(max_length=120)
    value: str
    source_tool: SourceTool


class Insight(BaseModel):
    """A conclusion supported by the data of the tools."""

    title: str = Field(max_length=120)
    description: str = Field(max_length=500)
    evidence: list[EvidenceItem] = Field(min_length=1, max_length=5)


class Recommendation(Insight):
    """An educational suggestion supported by the data of the tools."""


class Alert(Insight):
    """A point of attention supported by the data of the tools."""

    severity: Literal['info', 'warning', 'critical']


class AnalysisOutput(BaseModel):
    """Final financial analysis, written in Brazilian Portuguese."""

    main_insight: Insight
    insights: list[Insight] = Field(max_length=4)
    recommendations: list[Recommendation] = Field(min_length=1, max_length=5)
    alerts: list[Alert] = Field(max_length=3)
    data_limitations: list[str] = Field(max_length=5)
