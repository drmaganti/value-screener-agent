from __future__ import annotations

import pytest

from warren.engine import Warren
from warren.models import CategoryScores, DeepAnalysis, MetricSnapshot


class FakeMarketData:
    def __init__(self):
        self.calls: list[str] = []

    def fetch_metrics(self, ticker: str) -> MetricSnapshot:
        self.calls.append(ticker)
        if ticker == "FAIL":
            raise RuntimeError("provider failure")
        quality = 0.25 if ticker == "GOOD" else 0.08
        return MetricSnapshot(
            ticker=ticker,
            company_name=ticker,
            price=100,
            market_cap=1_000_000_000,
            trailing_pe=18 if ticker == "GOOD" else 45,
            forward_pe=17 if ticker == "GOOD" else 40,
            peg_ratio=1.2 if ticker == "GOOD" else 3.5,
            enterprise_to_ebitda=12 if ticker == "GOOD" else 28,
            free_cash_flow=100_000_000 if ticker == "GOOD" else -10_000_000,
            operating_cash_flow=120_000_000 if ticker == "GOOD" else -5_000_000,
            revenue_growth=0.20 if ticker == "GOOD" else 0.02,
            earnings_growth=0.18 if ticker == "GOOD" else -0.05,
            gross_margin=0.55 if ticker == "GOOD" else 0.18,
            operating_margin=0.22 if ticker == "GOOD" else 0.02,
            profit_margin=0.16 if ticker == "GOOD" else -0.02,
            return_on_equity=quality,
            return_on_assets=0.10 if ticker == "GOOD" else 0.01,
            debt_to_equity=40 if ticker == "GOOD" else 180,
            current_ratio=1.8 if ticker == "GOOD" else 0.8,
            beta=1.0,
            fifty_two_week_high=110,
            fifty_two_week_low=70,
            fifty_day_average=98,
            two_hundred_day_average=90,
        )


class FakeDeepAnalysis:
    def __init__(self):
        self.calls = 0

    async def analyze(self, metrics: MetricSnapshot, scores: CategoryScores):
        self.calls += 1
        return (
            DeepAnalysis(
                thesis="Test thesis",
                positives=["positive"],
                concerns=["concern"],
                bull_case=["bull"],
                bear_case=["bear"],
                risks=["risk"],
                what_would_change_view=["change"],
                verdict="Test verdict",
                confidence="medium",
            ),
            "fake-model",
        )


@pytest.mark.asyncio
async def test_screen_ranks_without_calling_deep_provider():
    market = FakeMarketData()
    deep = FakeDeepAnalysis()
    warren = Warren(market_data=market, deep_analysis=deep)

    response = await warren.screen(["WEAK", "GOOD"])

    assert response.screened_count == 2
    assert [item.ticker for item in response.results] == ["GOOD", "WEAK"]
    assert deep.calls == 0


@pytest.mark.asyncio
async def test_screen_deduplicates_and_isolates_failures():
    warren = Warren(market_data=FakeMarketData())

    response = await warren.screen(["GOOD", "GOOD", "FAIL", "WEAK"])

    assert response.screened_count == 3
    assert response.failed_tickers == ["FAIL"]
    assert {item.ticker for item in response.results} == {"GOOD", "WEAK"}


@pytest.mark.asyncio
async def test_deep_calls_deep_provider_once():
    market = FakeMarketData()
    deep = FakeDeepAnalysis()
    warren = Warren(market_data=market, deep_analysis=deep)

    response = await warren.deep("GOOD")

    assert response.ticker == "GOOD"
    assert response.analysis.verdict == "Test verdict"
    assert response.model == "fake-model"
    assert deep.calls == 1


@pytest.mark.asyncio
async def test_deep_requires_provider():
    warren = Warren(market_data=FakeMarketData())

    with pytest.raises(RuntimeError, match="DeepAnalysisProvider"):
        await warren.deep("GOOD")


@pytest.mark.asyncio
async def test_min_score_filters_results():
    warren = Warren(market_data=FakeMarketData())

    baseline = await warren.screen(["GOOD", "WEAK"])
    good_score = baseline.results[0].scores.overall
    weak_score = baseline.results[1].scores.overall
    threshold = (good_score + weak_score) / 2

    filtered = await warren.screen(["GOOD", "WEAK"], min_score=threshold)

    assert [item.ticker for item in filtered.results] == ["GOOD"]
