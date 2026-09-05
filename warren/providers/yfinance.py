from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from ..models import MetricSnapshot


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


class YFinanceMarketDataProvider:
    """Free development provider. Replaceable through the MarketDataProvider protocol."""

    def fetch_metrics(self, ticker: str) -> MetricSnapshot:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("ticker is required")

        stock = yf.Ticker(symbol)
        info = stock.info or {}
        price = _number(info.get("currentPrice") or info.get("regularMarketPrice"))
        if price is None:
            try:
                price = _number(stock.fast_info.last_price)
            except Exception:
                price = None

        historical_fcf: list[float] = []
        try:
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty and "Free Cash Flow" in cashflow.index:
                historical_fcf = [
                    number
                    for value in cashflow.loc["Free Cash Flow"].tolist()
                    if (number := _number(value)) is not None
                ]
                historical_fcf.reverse()
        except Exception:
            historical_fcf = []

        return MetricSnapshot(
            ticker=symbol,
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency"),
            price=price,
            market_cap=_number(info.get("marketCap")),
            trailing_pe=_number(info.get("trailingPE")),
            forward_pe=_number(info.get("forwardPE")),
            peg_ratio=_number(info.get("pegRatio")),
            price_to_book=_number(info.get("priceToBook")),
            enterprise_to_ebitda=_number(info.get("enterpriseToEbitda")),
            free_cash_flow=_number(info.get("freeCashflow")),
            operating_cash_flow=_number(info.get("operatingCashflow")),
            total_cash=_number(info.get("totalCash")),
            total_debt=_number(info.get("totalDebt")),
            shares_outstanding=_number(info.get("sharesOutstanding")),
            fetched_at=datetime.now(timezone.utc),
            historical_free_cash_flow=historical_fcf,
            revenue_growth=_number(info.get("revenueGrowth")),
            earnings_growth=_number(info.get("earningsGrowth")),
            gross_margin=_number(info.get("grossMargins")),
            operating_margin=_number(info.get("operatingMargins")),
            profit_margin=_number(info.get("profitMargins")),
            return_on_equity=_number(info.get("returnOnEquity")),
            return_on_assets=_number(info.get("returnOnAssets")),
            debt_to_equity=_number(info.get("debtToEquity")),
            current_ratio=_number(info.get("currentRatio")),
            beta=_number(info.get("beta")),
            fifty_two_week_high=_number(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=_number(info.get("fiftyTwoWeekLow")),
            fifty_day_average=_number(info.get("fiftyDayAverage")),
            two_hundred_day_average=_number(info.get("twoHundredDayAverage")),
        )
