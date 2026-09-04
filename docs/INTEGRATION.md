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

## Ask Warren product flow

```text
User enters a ticker or screens a universe
                |
           Warren Screen
                |
User requests full company research
                |
            Warren Deep
                |
Ask Warren renders scores + thesis + bull/bear/risk
```

The product interface should not duplicate Warren scoring, evidence collection or prompts. It owns presentation and user workflow while the engine owns the research methodology.

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
