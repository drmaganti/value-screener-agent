# Integration Guide

Warren is designed to support both in-process Python use and service-to-service HTTP use.

## Option 1: Python package

Best when the calling application can share the Python runtime/repository package.

```python
from warren import Warren
from warren.providers import YFinanceMarketDataProvider
from warren.deep import GeminiDeepAnalysisProvider

warren = Warren(
    market_data=YFinanceMarketDataProvider(),
    deep_analysis=GeminiDeepAnalysisProvider(),
)

screen = await warren.screen(
    ["AAPL", "MSFT", "NVDA"],
    top_n=10,
    min_score=60,
)

analysis = await warren.deep("NVDA")
```

## Option 2: HTTP service

Best when Warren is independently deployed and consumed by multiple products/languages.

```text
POST /v1/analyze
```

See `API.md` for request/response schemas.

## Parse integration

Recommended flow:

```text
User searches or discovers a stock in Parse
                |
       optional Warren Screen
                |
User requests / opens full stock research
                |
           Warren Deep
                |
Parse renders scores + thesis + bull/bear/risk
```

Parse should not duplicate Warren scoring or prompts. It should own presentation and product-specific workflow.

## Value Screener integration

If Value Screener is being used as a general discovery product:

```text
Value Screener universe / user filters
                |
           Warren Screen
                |
             ranking
                |
     optional Warren Deep
```

## Weekly Value Screen integration

The existing weekly strategy has its own thesis: find healthy large companies that have pulled back and may be temporarily mispriced.

Keep its strategy-specific rules outside Warren:

```text
~600-stock universe
       |
Weekly strategy cheap filters
- pullback / RSI
- market cap / liquidity
- earnings blackout
- prior-pick exclusion
- other strategy gates
       |
strategy survivors
       |
Warren Screen
- fundamentals
- valuation
- quality
- growth
- risk
- market context
       |
ranked finalists
       |
Warren Deep on a small N
       |
weekly report / logging
```

This preserves the Weekly Value Screen strategy while sharing the general analysis engine.

## Future applications

A caller should need to know only:

- which tickers to screen, or
- which single ticker to investigate deeply.

Potential integrations:

- watchlist health checks;
- portfolio research;
- earnings-event workflows;
- sector explorers;
- stock comparison tools;
- automated research reports.

## Provider swaps

To replace market data, implement:

```python
class MyProvider:
    def fetch_metrics(self, ticker: str) -> MetricSnapshot:
        ...
```

To replace deep analysis, implement:

```python
class MyDeepProvider:
    async def analyze(self, metrics, scores):
        return deep_analysis, model_name
```

Client applications should not change.

## Integration rule

Do not call Yahoo/Gemini directly from client applications for functionality Warren owns. That recreates coupling and makes methodology inconsistent across products.
