from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any

import yfinance as yf

from ..models import (
    EarningsHistoryEvidence,
    EstimateRevisionEvidence,
    EvidenceBundle,
    InsiderTransactionEvidence,
    MetricSnapshot,
    NewsEvidence,
    SourceStatus,
    TechnicalEvidence,
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


def _text(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if value != value:
            return None
    except Exception:
        pass
    result = str(value).strip()
    return result if result and result.lower() not in {"nan", "nat", "none"} else None


def _date_value(value: Any) -> date | datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if hasattr(value, "to_pydatetime"):
        try:
            converted = value.to_pydatetime()
            if isinstance(converted, datetime):
                return converted
        except Exception:
            pass
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


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
    """Development evidence provider backed by yfinance/Yahoo Finance.

    It supplies recent headlines, analyst estimates/revisions, earnings history,
    deterministic technical indicators and recent insider transactions. These are
    source facts; interpretation belongs to Warren's analysis layer.
    """

    HORIZONS = ("0q", "+1q", "0y", "+1y")

    def __init__(
        self,
        news_count: int = 8,
        earnings_history_count: int = 4,
        insider_transaction_count: int = 8,
    ):
        self.news_count = max(0, news_count)
        self.earnings_history_count = max(0, earnings_history_count)
        self.insider_transaction_count = max(0, insider_transaction_count)

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

        # Technical indicators are calculated deterministically from daily OHLCV.
        try:
            prices = stock.history(period="1y", interval="1d", auto_adjust=False)
            if prices is not None and not prices.empty and "Close" in prices.columns:
                close = prices["Close"].dropna()
                if not close.empty:
                    latest = _number(close.iloc[-1])
                    sma_50 = _number(close.rolling(50, min_periods=50).mean().iloc[-1])
                    sma_200 = _number(close.rolling(200, min_periods=200).mean().iloc[-1])

                    delta = close.diff()
                    gain = delta.clip(lower=0).rolling(14, min_periods=14).mean()
                    loss = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
                    gain_last = _number(gain.iloc[-1])
                    loss_last = _number(loss.iloc[-1])
                    if gain_last is None or loss_last is None:
                        rsi_14 = None
                    elif loss_last == 0:
                        rsi_14 = 100.0 if gain_last > 0 else 50.0
                    else:
                        rsi_14 = 100 - (100 / (1 + (gain_last / loss_last)))

                    ema_12 = close.ewm(span=12, adjust=False).mean()
                    ema_26 = close.ewm(span=26, adjust=False).mean()
                    macd_series = ema_12 - ema_26
                    signal_series = macd_series.ewm(span=9, adjust=False).mean()
                    macd = _number(macd_series.iloc[-1])
                    macd_signal = _number(signal_series.iloc[-1])

                    middle_20 = close.rolling(20, min_periods=20).mean()
                    std_20 = close.rolling(20, min_periods=20).std()
                    middle_last = _number(middle_20.iloc[-1])
                    std_last = _number(std_20.iloc[-1])
                    upper = middle_last + 2 * std_last if middle_last is not None and std_last is not None else None
                    lower = middle_last - 2 * std_last if middle_last is not None and std_last is not None else None

                    latest_volume = None
                    avg_volume_20 = None
                    if "Volume" in prices.columns:
                        volume = prices["Volume"].dropna()
                        if not volume.empty:
                            latest_volume = _number(volume.iloc[-1])
                            avg_volume_20 = _number(volume.tail(20).mean())

                    idx = close.index[-1]
                    as_of = idx.date() if hasattr(idx, "date") else None
                    bundle.technical.append(
                        TechnicalEvidence(
                            as_of=as_of,
                            close=latest,
                            sma_50=sma_50,
                            sma_200=sma_200,
                            rsi_14=_number(rsi_14),
                            macd=macd,
                            macd_signal=macd_signal,
                            bollinger_upper_20=_number(upper),
                            bollinger_lower_20=_number(lower),
                            latest_volume=latest_volume,
                            avg_volume_20=avg_volume_20,
                        )
                    )
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance technicals",
                    status="ok" if bundle.technical else "partial",
                    detail=f"{len(bundle.technical)} deterministic technical snapshot returned",
                )
            )
        except Exception as exc:
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance technicals",
                    status="error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )

        # Recent insider transactions add management/ownership context.
        try:
            insider_frame = stock.get_insider_transactions()
            if insider_frame is not None and not insider_frame.empty:
                if "Start Date" in insider_frame.columns:
                    insider_frame = insider_frame.sort_values("Start Date", ascending=False)
                for _, row in insider_frame.head(self.insider_transaction_count).iterrows():
                    evidence = InsiderTransactionEvidence(
                        insider=_text(row.get("Insider")),
                        position=_text(row.get("Position")),
                        transaction=_text(row.get("Transaction") or row.get("Text")),
                        start_date=_date_value(row.get("Start Date")),
                        shares=_number(row.get("Shares")),
                        value=_number(row.get("Value")),
                        ownership=_text(row.get("Ownership")),
                    )
                    values = evidence.model_dump(exclude={"source"}, exclude_none=True)
                    if values:
                        bundle.insider_transactions.append(evidence)
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance insider transactions",
                    status="ok" if bundle.insider_transactions else "partial",
                    detail=f"{len(bundle.insider_transactions)} recent insider transactions returned",
                )
            )
        except Exception as exc:
            bundle.source_status.append(
                SourceStatus(
                    source="Yahoo Finance insider transactions",
                    status="error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )

        return bundle
