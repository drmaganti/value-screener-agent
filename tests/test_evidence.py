from __future__ import annotations

from datetime import date

from warren.evidence import CompositeEvidenceProvider, EvidenceRouter, FredMacroEvidenceProvider, SecFilingEvidenceProvider
from warren.models import EvidenceBundle, FilingEvidence, MetricSnapshot, NewsEvidence, SourceStatus


class GoodProvider:
    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        return EvidenceBundle(
            news=[NewsEvidence(title="Grounded headline")],
            source_status=[SourceStatus(source="good", status="ok")],
        )


class BadProvider:
    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        raise RuntimeError("boom")


class DuplicateNewsProvider:
    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        return EvidenceBundle(
            filings=[
                FilingEvidence(
                    form="10-Q",
                    filed_at=date(2026, 7, 31),
                    accession_number="0000000000-26-000001",
                    url="https://www.sec.gov/example?tracking=1",
                )
            ],
            news=[
                NewsEvidence(
                    title="Company raises full-year guidance",
                    publisher="Publisher A",
                    url="https://example.com/story?utm_source=a",
                ),
                NewsEvidence(
                    title="Company raises full year guidance!",
                    publisher="Publisher B",
                    url="https://example.org/story?utm_source=b",
                ),
            ],
            source_status=[SourceStatus(source="test", status="ok")],
        )


def test_composite_preserves_good_evidence_when_one_source_fails():
    provider = CompositeEvidenceProvider([GoodProvider(), BadProvider()])
    bundle = provider.fetch_evidence("AAPL", MetricSnapshot(ticker="AAPL"))

    assert bundle.news[0].title == "Grounded headline"
    assert any(status.status == "error" for status in bundle.source_status)


def test_evidence_router_normalizes_and_deduplicates_claims():
    provider = EvidenceRouter(DuplicateNewsProvider())
    bundle = provider.fetch_evidence("AAPL", MetricSnapshot(ticker="AAPL"))

    assert len(bundle.news) == 2
    assert len(bundle.claims) == 2

    news_claim = next(claim for claim in bundle.claims if claim.category == "news")
    assert news_claim.retrieval_depth == "headline"
    assert news_claim.authority_tier == 4
    assert news_claim.duplicate_count == 1
    assert news_claim.independent_source_count == 2
    assert news_claim.confidence == "low"

    filing_claim = next(claim for claim in bundle.claims if claim.category == "filing")
    assert filing_claim.authority_tier == 1
    assert filing_claim.retrieval_depth == "metadata"
    assert filing_claim.metadata["content_retrieved"] is False

    router_meta = bundle.metadata["evidence_router"]
    assert router_meta["raw_items"] == 3
    assert router_meta["normalized_claims"] == 2
    assert router_meta["deduplicated_items"] == 1


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
