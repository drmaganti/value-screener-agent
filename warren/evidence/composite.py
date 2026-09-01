from __future__ import annotations

from ..models import EvidenceBundle, MetricSnapshot, SourceStatus
from ..protocols import EvidenceProvider


class CompositeEvidenceProvider:
    """Combines independent evidence sources without making Deep all-or-nothing.

    A failed source is recorded in `source_status`; evidence from other sources
    remains usable. This is deliberate because filings, news, estimates and macro
    data have different availability and failure modes.
    """

    def __init__(self, providers: list[EvidenceProvider]):
        self.providers = providers

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        bundle = EvidenceBundle()
        for provider in self.providers:
            try:
                bundle = bundle.merge(provider.fetch_evidence(ticker, metrics))
            except Exception as exc:
                bundle.source_status.append(
                    SourceStatus(
                        source=provider.__class__.__name__,
                        status="error",
                        detail=f"{type(exc).__name__}: {exc}",
                    )
                )
        return bundle
