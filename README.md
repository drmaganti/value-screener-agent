# Warren

Warren is a reusable stock-intelligence engine designed to be called by any product that needs stock screening or deeper investment research.

It is intentionally **not tied to Parse, Value Screener, a specific UI, a specific market-data vendor, or a specific LLM**.

> Research software only. Warren does not provide personalized investment advice or execute trades.

## Why Warren exists

Most stock tools either rank companies with opaque scores or ask one LLM to produce an unchallenged narrative. Warren separates these jobs:

- **Screen mode** cheaply ranks a universe using verified structured data and deterministic scoring.
- **Deep mode** investigates one company using independent bull, bear and risk perspectives followed by a final synthesis.

This preserves the strongest design idea from TradingAgents while avoiding multi-agent cost across an entire index.

## Modes

### Screen

Use when the question is: **Which stocks deserve further research?**

```json
{
  "mode": "screen",
  "tickers": ["AAPL", "MSFT", "NVDA", "GOOG"],
  "top_n": 20,
  "min_score": 60
}
```

Screen mode:

- makes no LLM calls;
- scores fundamentals, valuation, business quality, growth, risk resilience and market context;
- ranks a caller-supplied universe;
- can be used inside a weekly strategy funnel, Parse, Value Screener or another future product.

### Deep

Use when the question is: **I am interested in this company. What is the investment argument and what could be wrong with it?**

```json
{
  "mode": "deep",
  "ticker": "NVDA"
}
```

Deep mode currently runs:

```text
Verified structured evidence
        |
Deterministic scoring
        |
  +-----+------+-------+
  |            |       |
Bull analyst  Bear    Risk reviewer
  |            |       |
  +------------+-------+
               |
        Final evaluator
               |
Thesis / positives / concerns / risks /
what changes the view / verdict / confidence
```

## Reusable Python API

```python
from warren import Warren
from warren.providers import YFinanceMarketDataProvider
from warren.deep import GeminiDeepAnalysisProvider

warren = Warren(
    market_data=YFinanceMarketDataProvider(),
    deep_analysis=GeminiDeepAnalysisProvider(),
)

screen = await warren.screen(["AAPL", "MSFT", "NVDA"])
deep = await warren.deep("NVDA")
```

The provider interfaces are deliberately replaceable. A future application can use Polygon, FMP, Alpha Vantage, licensed fundamentals, another LLM, or a non-LLM deep-analysis implementation without changing Warren's caller contract.

## HTTP API

The FastAPI adapter exposes:

- `GET /health`
- `POST /v1/analyze`

See [docs/API.md](docs/API.md).

## Documentation

- [Product definition](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/API.md)
- [Methodology](docs/METHODOLOGY.md)
- [Integration guide](docs/INTEGRATION.md)
- [Evaluation strategy](docs/EVALUATION.md)
- [Risks and limitations](docs/RISKS.md)
- [Security](SECURITY.md)
- [Roadmap](docs/ROADMAP.md)
- [Naming / trademark notes](docs/NAMING.md)

## Current status

Warren is an early product module. The current implementation establishes the reusable boundaries and the two-mode contract. Before relying on scores for production investment research, the methodology needs calibration/backtesting and Deep mode needs additional verified evidence sources such as filings, news/macro and estimate revisions.

## Configuration

Deep mode currently expects:

```bash
export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-2.5-flash"   # optional
```

Screen mode does not require an LLM key.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

OpenAPI documentation is available from FastAPI at `/docs` when running locally.
