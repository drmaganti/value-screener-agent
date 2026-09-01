from __future__ import annotations

import math
import os
from datetime import date
from typing import Any

import httpx

from ..models import EvidenceBundle, MacroEvidence, MetricSnapshot, SourceStatus


class FredMacroEvidenceProvider:
    """Optional macro context from FRED.

    FRED requires an API key. If no key is configured, Warren records the source
    as unavailable and continues Deep with the remaining evidence.
    """

    ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"
    DEFAULT_SERIES = {
        "DGS10": ("US 10-year Treasury yield", "percent", 1, "previous observation"),
        "DFF": ("Effective federal funds rate", "percent", 1, "previous observation"),
        "UNRATE": ("US unemployment rate", "percent", 1, "previous observation"),
        "CPIAUCSL": ("US Consumer Price Index", "index 1982-84=100", 12, "approximately 12 observations ago"),
    }

    def __init__(
        self,
        api_key: str | None = None,
        series: dict[str, tuple[str, str, int, str]] | None = None,
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.series = series or self.DEFAULT_SERIES
        self.timeout = timeout

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if math.isfinite(result) else None

    @staticmethod
    def _date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        bundle = EvidenceBundle()
        if not self.api_key:
            bundle.source_status.append(
                SourceStatus(
                    source="FRED",
                    status="unavailable",
                    detail="FRED_API_KEY is not configured; macro evidence skipped.",
                )
            )
            return bundle

        with httpx.Client(timeout=self.timeout) as client:
            for series_id, (label, units, lookback, prior_period) in self.series.items():
                try:
                    response = client.get(
                        self.ENDPOINT,
                        params={
                            "series_id": series_id,
                            "api_key": self.api_key,
                            "file_type": "json",
                            "sort_order": "desc",
                            "limit": max(lookback + 4, 16),
                        },
                    )
                    response.raise_for_status()
                    observations = response.json().get("observations") or []
                    clean: list[tuple[date | None, float]] = []
                    for observation in observations:
                        number = self._number(observation.get("value"))
                        if number is None:
                            continue
                        clean.append((self._date(observation.get("date")), number))
                    if not clean:
                        continue
                    latest_date, latest = clean[0]
                    prior = clean[lookback][1] if len(clean) > lookback else None
                    bundle.macro.append(
                        MacroEvidence(
                            series_id=series_id,
                            label=label,
                            value=latest,
                            prior_value=prior,
                            prior_period=prior_period if prior is not None else None,
                            as_of=latest_date,
                            units=units,
                        )
                    )
                except Exception as exc:
                    bundle.source_status.append(
                        SourceStatus(
                            source=f"FRED {series_id}",
                            status="error",
                            detail=f"{type(exc).__name__}: {exc}",
                        )
                    )

        bundle.source_status.append(
            SourceStatus(
                source="FRED",
                status="ok" if bundle.macro else "partial",
                detail=f"{len(bundle.macro)} macro series returned",
            )
        )
        return bundle
