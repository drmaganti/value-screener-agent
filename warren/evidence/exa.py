from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from ..models import EvidenceBundle, MetricSnapshot, SourceStatus, WebEvidence


class ExaWebEvidenceProvider:
    """Optional pay-as-you-go web discovery for material company developments.

    Warren requests query-relevant excerpts rather than full pages to constrain
    latency, provider cost and prompt size. Exa is an additional discovery layer,
    not a replacement for primary SEC/company evidence.
    """

    SEARCH_URL = "https://api.exa.ai/search"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        num_results: int = 6,
        highlight_characters: int = 700,
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        self.num_results = min(max(1, num_results), 10)
        self.highlight_characters = min(max(200, highlight_characters), 2000)
        self.timeout = timeout

    @staticmethod
    def _published_at(raw: Any) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _query(ticker: str, metrics: MetricSnapshot) -> str:
        company = metrics.company_name or ticker
        return (
            f"Latest material developments for {company} ({ticker}) relevant to an investor: "
            "earnings and guidance, investor relations updates, major product or strategy changes, "
            "regulation or litigation, competition, and industry demand. Prefer recent primary "
            "sources and reputable financial journalism; avoid duplicate or syndicated coverage."
        )

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        bundle = EvidenceBundle()
        if not self.api_key:
            bundle.source_status.append(
                SourceStatus(
                    source="Exa web discovery",
                    status="unavailable",
                    detail="EXA_API_KEY is not configured; web discovery skipped.",
                )
            )
            return bundle

        query = self._query(ticker.strip().upper(), metrics)
        body = {
            "query": query,
            "type": "auto",
            "numResults": self.num_results,
            "userLocation": "US",
            "moderation": True,
            "contents": {
                "highlights": {"maxCharacters": self.highlight_characters},
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.post(self.SEARCH_URL, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()

        seen_urls: set[str] = set()
        for result in payload.get("results") or []:
            url = str(result.get("url") or "").strip()
            title = str(result.get("title") or "").strip()
            if not url or not title or url in seen_urls:
                continue
            seen_urls.add(url)
            highlights = [
                str(value).strip()
                for value in (result.get("highlights") or [])
                if str(value).strip()
            ]
            bundle.web.append(
                WebEvidence(
                    title=title,
                    url=url,
                    published_at=self._published_at(result.get("publishedDate")),
                    author=str(result.get("author")).strip() if result.get("author") else None,
                    highlights=highlights[:3],
                    query=query,
                )
            )

        cost = ((payload.get("costDollars") or {}).get("total"))
        if isinstance(cost, (int, float)):
            bundle.metadata["exa_cost_dollars"] = float(cost)
        if payload.get("requestId"):
            bundle.metadata["exa_request_id"] = str(payload["requestId"])

        bundle.source_status.append(
            SourceStatus(
                source="Exa web discovery",
                status="ok" if bundle.web else "partial",
                detail=f"{len(bundle.web)} web results with query-relevant excerpts returned",
            )
        )
        return bundle
