from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from ..models import (
    EarningsHistoryEvidence,
    EstimateRevisionEvidence,
    EvidenceBundle,
    MetricSnapshot,
    NewsEvidence,
    SourceStatus,
)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _cell(frame, row: str, column: str):
    try:
        value = frame.loc[row, column]
    except Exception:
        return None
    return None if value is None else value


def _published_at(item: dict) -> datetime | None:
    content = item.get("content") or item
    raw = content.get("pubDate") or item.get("pubDate")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    epoch = item.get("providerPublishTime")
    if epoch:
        try:
            return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    return None


def _news_url(item: dict) -> str | None:
    content = item.get("content") or item
    for key in ("canonicalUrl", "clickThroughUrl"):
        candidate = content.get(key)
        if isinstance(candidate, dict) and candidate.get("url"):
            return str(candidate["url"])
    for key in ("link", "url"):
        if item.get(key):
            return str(item[key])
    return None


class YahooEvidenceProvider:
    """Recent headlines plus analyst estimate/revision evidence from yfinance.

    This provider deliberately returns source facts only. Warren's LLM layer may
    interpret those facts but may not replace or fabricate them.
    """

    HORIZONS = ("0q", "+1q", "0y", "+1y")

    def __init__(self, news_count: int = 8, earnings_history_count: int = 4):
        self.news_count = max(0, news_count)
        self.earnings_history_count = max(0, earnings_history_count)

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        symbol = ticker.strip().upper()
        stock = yf.Ticker(symbol)
        bundle = EvidenceBundle(metadata={"yahoo_symbol": symbol})

        # Recent news / press coverage.
        try:
            raw_news = stock.get_news(count=self.news_count, tab="news") or []
            for item in raw_news[: self.news_count]:
                content = item.get("content") or item
                title = content.get("title") or item.get("title")
                if not title:
                    continue
                provider = content.get("provider")
                publisher = provider.get("displayName") if isinstance(provider, dict) else item.get("publisher")
                bundle.news.append(
                    NewsEvidence(
                        title=str(title),
                        publisher=str(publisher) if publisher else None,
                        published_at=_published_at(item),
                        url=_news_url(item),
                    )
                )
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance news",
                    status="ok" if bundle.news else "partial",
                    detail=f"{len(bundle.news)} recent headlines returned",
                )
            )
        except Exception as exc:
            bundle.source_status.append(
                SourceStatus(source="Yahoo Finance news", status="error", detail=f"{type(exc).__name__}: {exc}")
            )

        # Estimate levels, trends and analyst revision counts.
        try:
            eps_trend = stock.get_eps_trend()
            eps_revisions = stock.get_eps_revisions()
            earnings_estimate = stock.get_earnings_estimate()
            revenue_estimate = stock.get_revenue_estimate()

            for horizon in self.HORIZONS:
                evidence = EstimateRevisionEvidence(
                    horizon=horizon,
                    analyst_count=_integer(_cell(earnings_estimate, horizon, "numberOfAnalysts")),
                    eps_current=_number(_cell(eps_trend, horizon, "current")),
                    eps_7d_ago=_number(_cell(eps_trend, horizon, "7daysAgo")),
                    eps_30d_ago=_number(_cell(eps_trend, horizon, "30daysAgo")),
                    eps_60d_ago=_number(_cell(eps_trend, horizon, "60daysAgo")),
                    eps_90d_ago=_number(_cell(eps_trend, horizon, "90daysAgo")),
                    eps_up_7d=_integer(_cell(eps_revisions, horizon, "upLast7days")),
                    eps_down_7d=_integer(_cell(eps_revisions, horizon, "downLast7days")),
                    eps_up_30d=_integer(_cell(eps_revisions, horizon, "upLast30days")),
                    eps_down_30d=_integer(_cell(eps_revisions, horizon, "downLast30days")),
                    earnings_growth=_number(_cell(earnings_estimate, horizon, "growth")),
                    revenue_growth=_number(_cell(revenue_estimate, horizon, "growth")),
                )
                values = evidence.model_dump(exclude={"horizon", "source"}, exclude_none=True)
                if values:
                    bundle.estimate_revisions.append(evidence)

            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance analyst estimates",
                    status="ok" if bundle.estimate_revisions else "partial",
                    detail=f"{len(bundle.estimate_revisions)} estimate horizons returned",
                )
            )
        except Exception as exc:
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance analyst estimates",
                    status="error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )

        # Actual-versus-estimate history provides context on recent execution.
        try:
            history = stock.get_earnings_history()
            if history is not None and not history.empty:
                history = history.sort_index(ascending=False).head(self.earnings_history_count)
                for idx, row in history.iterrows():
                    try:
                        period = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
                    except Exception:
                        period = None
                    bundle.earnings_history.append(
                        EarningsHistoryEvidence(
                            period=period if isinstance(period, datetime) else None,
                            eps_estimate=_number(row.get("epsEstimate")),
                            eps_actual=_number(row.get("epsActual")),
                            eps_difference=_number(row.get("epsDifference")),
                            surprise_percent=_number(row.get("surprisePercent")),
                        )
                    )
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance earnings history",
                    status="ok" if bundle.earnings_history else "partial",
                    detail=f"{len(bundle.earnings_history)} earnings periods returned",
                )
            )
        except Exception as exc:
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance earnings history",
                    status="error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )

        return bundle
