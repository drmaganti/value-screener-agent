from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    mode: Literal["screen", "deep"]
    ticker: str | None = Field(default=None, min_length=1, max_length=20)
    tickers: list[str] | None = Field(default=None, min_length=1, max_length=1000)
    top_n: int = Field(default=25, ge=1, le=100)
    min_score: float = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_mode_inputs(self):
        if self.mode == "deep":
            if not self.ticker:
                raise ValueError("ticker is required when mode='deep'")
            if self.tickers:
                raise ValueError("tickers is only valid when mode='screen'")
        else:
            if not self.tickers:
                raise ValueError("tickers is required when mode='screen'")
            if self.ticker:
                raise ValueError("ticker is only valid when mode='deep'")
        return self


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
    mode: Literal["screen", "deep"]
    ticker: str | None = None
    screened_count: int | None = None
    failed_tickers: list[str] = []
    results: list[ScreenResult] | None = None
    metrics: MetricSnapshot | None = None
    scores: CategoryScores | None = None
    missing_data: list[str] = []
    analysis: DeepAnalysis | None = None
    model: str | None = None
    disclaimer: str = "For research purposes only. Not financial advice."
