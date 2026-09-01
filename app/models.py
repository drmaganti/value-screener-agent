from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    mode: Literal["screen", "deep"] = "screen"
    depth: Literal["standard", "debate"] = "standard"


class MetricSnapshot(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    currency: str | None = None
    price: float | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    enterprise_to_ebitda: float | None = None
    free_cash_flow: float | None = None
    operating_cash_flow: float | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    profit_margin: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    beta: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    fifty_day_average: float | None = None
    two_hundred_day_average: float | None = None


class CategoryScores(BaseModel):
    fundamentals: float
    valuation: float
    business_quality: float
    growth: float
    risk_resilience: float
    market_context: float
    overall: float


class DeepAnalysis(BaseModel):
    thesis: str
    positives: list[str]
    concerns: list[str]
    bull_case: list[str]
    bear_case: list[str]
    risks: list[str]
    what_would_change_view: list[str]
    verdict: str
    confidence: Literal["low", "medium", "high"]


class AnalyzeResponse(BaseModel):
    ticker: str
    mode: Literal["screen", "deep"]
    depth: Literal["standard", "debate"]
    metrics: MetricSnapshot
    scores: CategoryScores
    missing_data: list[str]
    analysis: DeepAnalysis | None = None
    model: str | None = None
    disclaimer: str = "For research purposes only. Not financial advice."
