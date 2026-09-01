from __future__ import annotations

from typing import Protocol

from .models import CategoryScores, DeepAnalysis, EvidenceBundle, MetricSnapshot


class MarketDataProvider(Protocol):
    """Supplies verified structured market/fundamental data to Warren."""

    def fetch_metrics(self, ticker: str) -> MetricSnapshot: ...


class EvidenceProvider(Protocol):
    """Collects source-attributed evidence used only by Warren Deep."""

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle: ...


class DeepAnalysisProvider(Protocol):
    """Produces bull/bear/risk synthesis from verified structured evidence."""

    async def analyze(
        self,
        metrics: MetricSnapshot,
        scores: CategoryScores,
        evidence: EvidenceBundle,
    ) -> tuple[DeepAnalysis, str | None]: ...
