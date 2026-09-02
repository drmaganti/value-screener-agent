from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit

from ..models import (
    EarningsHistoryEvidence,
    EstimateRevisionEvidence,
    EvidenceBundle,
    EvidenceClaim,
    EvidenceReference,
    FilingEvidence,
    MacroEvidence,
    MetricSnapshot,
    NewsEvidence,
)
from ..protocols import EvidenceProvider


class EvidenceRouter:
    """Normalizes heterogeneous evidence into reusable, deduplicated claims.

    Raw provider objects remain in the EvidenceBundle for transparency and
    backward compatibility. `claims` is the interpretation-ready layer shared by
    Bull, Bear, Risk and Final analysis.
    """

    VERSION = "1.0"

    def __init__(self, upstream: EvidenceProvider):
        self.upstream = upstream

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        bundle = self.upstream.fetch_evidence(ticker, metrics)
        claims, duplicate_count = normalize_claims(bundle)
        bundle.claims = claims
        bundle.metadata["evidence_router"] = {
            "version": self.VERSION,
            "raw_items": _raw_item_count(bundle),
            "normalized_claims": len(claims),
            "deduplicated_items": duplicate_count,
            "claim_categories": sorted({claim.category for claim in claims}),
        }
        return bundle


def _raw_item_count(bundle: EvidenceBundle) -> int:
    return (
        len(bundle.filings)
        + len(bundle.news)
        + len(bundle.estimate_revisions)
        + len(bundle.earnings_history)
        + len(bundle.macro)
    )


def _stable_id(category: str, key: str) -> str:
    digest = hashlib.sha256(f"{category}:{key}".encode("utf-8")).hexdigest()[:16]
    return f"{category}:{digest}"


def _canonical_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
    except ValueError:
        return url


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _reference(
    source: str,
    *,
    publisher: str | None = None,
    url: str | None = None,
    authority_tier: int,
    retrieval_depth: str,
) -> EvidenceReference:
    return EvidenceReference(
        source=source,
        publisher=publisher,
        url=_canonical_url(url),
        authority_tier=authority_tier,
        retrieval_depth=retrieval_depth,
    )


def _confidence(authority_tier: int, retrieval_depth: str, independent_sources: int = 1) -> str:
    if retrieval_depth == "structured" and authority_tier <= 2:
        return "high"
    if retrieval_depth == "full_text" and authority_tier <= 3:
        return "high"
    if independent_sources >= 2 and authority_tier <= 3:
        return "high"
    if retrieval_depth == "headline":
        return "low"
    if authority_tier <= 2:
        return "medium"
    return "low"


def _filing_claim(item: FilingEvidence) -> EvidenceClaim:
    filed = item.filed_at.isoformat() if item.filed_at else "an unknown date"
    key = item.accession_number or f"{item.form}:{filed}:{item.primary_document or ''}"
    return EvidenceClaim(
        id=_stable_id("filing", key),
        category="filing",
        claim=f"SEC filing metadata shows a {item.form} filed on {filed}.",
        as_of=item.filed_at,
        authority_tier=1,
        retrieval_depth="metadata",
        confidence="medium",
        references=[
            _reference(
                item.source,
                url=item.url,
                authority_tier=1,
                retrieval_depth="metadata",
            )
        ],
        metadata={
            "form": item.form,
            "accession_number": item.accession_number,
            "primary_document": item.primary_document,
            "content_retrieved": False,
        },
    )


def _news_claim(group: list[NewsEvidence]) -> EvidenceClaim:
    first = group[0]
    publishers = {item.publisher or item.source for item in group}
    independent = len(publishers)
    references = [
        _reference(
            item.source,
            publisher=item.publisher,
            url=item.url,
            authority_tier=4,
            retrieval_depth="headline",
        )
        for item in group
    ]
    return EvidenceClaim(
        id=_stable_id("news", _normalize_text(first.title)),
        category="news",
        claim=f'Published headline: "{first.title}"',
        as_of=first.published_at,
        authority_tier=4,
        retrieval_depth="headline",
        confidence=_confidence(4, "headline", independent),
        references=references,
        independent_source_count=independent,
        duplicate_count=max(0, len(group) - 1),
        metadata={
            "headline_only": True,
            "publisher_count": independent,
            "content_retrieved": False,
        },
    )


def _estimate_claim(item: EstimateRevisionEvidence) -> EvidenceClaim:
    parts = [f"For {item.horizon}, the current EPS estimate is {item.eps_current!r}."]
    if item.eps_30d_ago is not None:
        parts.append(f"The 30-day-ago EPS estimate was {item.eps_30d_ago!r}.")
    if item.analyst_count is not None:
        parts.append(f"The reported analyst count is {item.analyst_count}.")
    return EvidenceClaim(
        id=_stable_id("estimate_revision", item.horizon),
        category="estimate_revision",
        claim=" ".join(parts),
        authority_tier=2,
        retrieval_depth="structured",
        confidence="high",
        references=[
            _reference(
                item.source,
                authority_tier=2,
                retrieval_depth="structured",
            )
        ],
        metadata=item.model_dump(exclude_none=True, mode="json"),
    )


def _earnings_claim(item: EarningsHistoryEvidence) -> EvidenceClaim:
    period = item.period.date().isoformat() if item.period else "unknown period"
    return EvidenceClaim(
        id=_stable_id("earnings", period),
        category="earnings",
        claim=(
            f"For the earnings period {period}, reported EPS was {item.eps_actual!r} "
            f"versus an estimate of {item.eps_estimate!r}."
        ),
        as_of=item.period,
        authority_tier=2,
        retrieval_depth="structured",
        confidence="high",
        references=[
            _reference(
                item.source,
                authority_tier=2,
                retrieval_depth="structured",
            )
        ],
        metadata=item.model_dump(exclude_none=True, mode="json"),
    )


def _macro_claim(item: MacroEvidence) -> EvidenceClaim:
    units = f" {item.units}" if item.units else ""
    return EvidenceClaim(
        id=_stable_id("macro", f"{item.series_id}:{item.as_of or ''}"),
        category="macro",
        claim=f"FRED series {item.series_id} ({item.label}) is {item.value}{units} as of {item.as_of or 'the reported date'}.",
        as_of=item.as_of,
        authority_tier=1,
        retrieval_depth="structured",
        confidence="high",
        references=[
            _reference(
                item.source,
                authority_tier=1,
                retrieval_depth="structured",
            )
        ],
        metadata=item.model_dump(exclude_none=True, mode="json"),
    )


def normalize_claims(bundle: EvidenceBundle) -> tuple[list[EvidenceClaim], int]:
    claims: list[EvidenceClaim] = []

    claims.extend(_filing_claim(item) for item in bundle.filings)
    claims.extend(_estimate_claim(item) for item in bundle.estimate_revisions)
    claims.extend(_earnings_claim(item) for item in bundle.earnings_history)
    claims.extend(_macro_claim(item) for item in bundle.macro)

    grouped_news: dict[str, list[NewsEvidence]] = defaultdict(list)
    for item in bundle.news:
        grouped_news[_normalize_text(item.title)].append(item)
    claims.extend(_news_claim(group) for group in grouped_news.values())

    claims.sort(key=lambda claim: (claim.authority_tier, claim.category, claim.id))
    duplicate_count = sum(claim.duplicate_count for claim in claims)
    return claims, duplicate_count
