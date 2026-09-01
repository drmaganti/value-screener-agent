from __future__ import annotations

from warren.evidence import CompositeEvidenceProvider, FredMacroEvidenceProvider, SecFilingEvidenceProvider
from warren.models import EvidenceBundle, MetricSnapshot, NewsEvidence, SourceStatus


class GoodProvider:
    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        return EvidenceBundle(
            news=[NewsEvidence(title="Grounded headline")],
            source_status=[SourceStatus(source="good", status="ok")],
        )


class BadProvider:
    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        raise RuntimeError("boom")


def test_composite_preserves_good_evidence_when_one_source_fails():
    provider = CompositeEvidenceProvider([GoodProvider(), BadProvider()])
    bundle = provider.fetch_evidence("AAPL", MetricSnapshot(ticker="AAPL"))

    assert bundle.news[0].title == "Grounded headline"
    assert any(status.status == "error" for status in bundle.source_status)


def test_fred_without_key_degrades_to_unavailable(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    provider = FredMacroEvidenceProvider(api_key=None)

    bundle = provider.fetch_evidence("AAPL", MetricSnapshot(ticker="AAPL"))

    assert bundle.macro == []
    assert bundle.source_status[0].source == "FRED"
    assert bundle.source_status[0].status == "unavailable"


def test_sec_does_not_guess_cross_listing_for_tsx():
    provider = SecFilingEvidenceProvider()

    bundle = provider.fetch_evidence("RY.TO", MetricSnapshot(ticker="RY.TO"))

    assert bundle.filings == []
    assert bundle.source_status[0].source == "SEC EDGAR"
    assert bundle.source_status[0].status == "unavailable"
