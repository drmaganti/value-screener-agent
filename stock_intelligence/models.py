from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


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


class ScreenResult(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    price: float | None = None
    scores: CategoryScores
    missing_data_count: int = 0


class ScreenOutput(BaseModel):
    screened_count: int
    failed_tickers: list[str]
    results: list[ScreenResult]


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


class DeepOutput(BaseModel):
    ticker: str
    metrics: MetricSnapshot
    scores: CategoryScores
    missing_data: list[str]
    analysis: DeepAnalysis
    model: str | None = None
