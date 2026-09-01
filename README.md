# Warren

Warren is a reusable stock-intelligence engine designed to be called by any product that needs stock screening or deeper investment research.

It is intentionally **not tied to Parse, Value Screener, a specific UI, a specific market-data vendor, or a specific LLM**.

> Research software only. Warren does not provide personalized investment advice or execute trades.

## Why Warren exists

Most stock tools either rank companies with opaque scores or ask one LLM to produce an unchallenged narrative. Warren separates these jobs:

- **Screen mode** cheaply ranks a universe using structured data and deterministic scoring.
- **Deep mode** investigates one company using source-attributed evidence, independent bull/bear/risk perspectives, and final synthesis.

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
- does not collect news, filings or macro evidence;
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
Structured company metrics
          +
Source-attributed evidence
  |-- SEC recent filing metadata
  |-- Yahoo recent news headlines
  |-- Yahoo EPS/revenue estimates + revisions
  |-- Yahoo earnings surprise history
  `-- FRED macro observations (optional)
          |
Deterministic scoring
          |
   +------+------+------+
   |             |      |
 Bull analyst   Bear   Risk reviewer
   |             |      |
   +-------------+------+
                 |
          Final evaluator
                 |
Thesis / positives / concerns / risks /
what changes the view / verdict / confidence
```

### Evidence discipline

Warren treats source material according to what was actually retrieved:

- SEC entries are **filing metadata**, not filing-content summaries. Deep must not claim what a filing says unless filing text is added as a future evidence source.
- Yahoo news entries are **headlines**, not full-article content. Deep must not infer facts beyond the headline.
- Estimate revisions, earnings history and FRED observations are structured values and can be compared directly.
- Every evidence source reports `ok`, `partial`, `unavailable` or `error`; missing sources reduce confidence rather than silently disappearing.

## Reusable Python API

```python
from warren import Warren
from warren.deep import GeminiDeepAnalysisProvider
from warren.evidence import (
    CompositeEvidenceProvider,
    FredMacroEvidenceProvider,
    SecFilingEvidenceProvider,
    YahooEvidenceProvider,
)
from warren.providers import YFinanceMarketDataProvider

warren = Warren(
    market_data=YFinanceMarketDataProvider(),
    deep_analysis=GeminiDeepAnalysisProvider(),
    evidence=CompositeEvidenceProvider([
        SecFilingEvidenceProvider(),
        YahooEvidenceProvider(),
        FredMacroEvidenceProvider(),
    ]),
)

screen = await warren.screen(["AAPL", "MSFT", "NVDA"])
deep = await warren.deep("NVDA")
```

The provider interfaces are deliberately replaceable. A future application can use Polygon, FMP, licensed fundamentals, a paid news feed, another macro provider, another LLM, or a non-LLM deep-analysis implementation without changing Warren's caller contract.

## HTTP API

The FastAPI adapter exposes:

- `GET /health`
- `POST /v1/analyze`

Deep responses include the exact `evidence` packet used for analysis so clients can display provenance and evidence availability.

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

**v0.3** establishes the reusable evidence layer and grounds Deep mode in filings metadata, news headlines, analyst estimate revisions, recent earnings history and optional macro data.

Still required before production investment-research reliance:

- score calibration/backtesting;
- primary-source filing text/XBRL extraction rather than metadata alone;
- production/SLA-backed market and news providers;
- evidence freshness/caching policy;
- methodology/model versioning;
- deeper evaluation of factuality and investment usefulness.

## Configuration

```bash
# Required for Deep synthesis
export GEMINI_API_KEY="..."

# Optional model override
export GEMINI_MODEL="gemini-2.5-flash"

# Optional macro evidence. Deep continues without it when absent.
export FRED_API_KEY="..."

# Recommended for production automated SEC access.
export SEC_USER_AGENT="WarrenStockIntelligence/0.3 contact@example.com"
```

Screen mode does not require an LLM key or evidence-provider keys.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
uvicorn app.main:app --reload
```

OpenAPI documentation is available from FastAPI at `/docs` when running locally.
