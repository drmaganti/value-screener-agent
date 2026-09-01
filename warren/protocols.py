from __future__ import annotations

from typing import Protocol

from .models import CategoryScores, DeepAnalysis, MetricSnapshot


class MarketDataProvider(Protocol):
    """Supplies verified structured market/fundamental data to Warren."""

    def fetch_metrics(self, ticker: str) -> MetricSnapshot: ...


class DeepAnalysisProvider(Protocol):
    """Produces the expensive bull/bear/risk synthesis from verified evidence."""

    async def analyze(
        self,
        metrics: MetricSnapshot,
        scores: CategoryScores,
    ) -> tuple[DeepAnalysis, str | None]: ...
