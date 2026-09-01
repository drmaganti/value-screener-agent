# API Contract

## Base endpoint

`POST /v1/analyze`

The `mode` field selects one of two different jobs. Mode-specific validation prevents a caller from accidentally screening one ticker or running Deep against an entire universe.

## Screen mode

### Request

```json
{
  "mode": "screen",
  "tickers": ["AAPL", "MSFT", "NVDA", "GOOG"],
  "top_n": 20,
  "min_score": 60
}
```

Rules:

- `tickers` is required.
- `ticker` must not be supplied.
- Maximum current request size: 1,000 symbols.
- `top_n`: 1-100, default 25.
- `min_score`: 0-100, default 0.
- Duplicate tickers are removed while preserving first appearance.

### Response

```json
{
  "mode": "screen",
  "screened_count": 4,
  "failed_tickers": [],
  "results": [
    {
      "ticker": "MSFT",
      "company_name": "Microsoft Corporation",
      "sector": "Technology",
      "price": 0,
      "scores": {
        "fundamentals": 0,
        "valuation": 0,
        "business_quality": 0,
        "growth": 0,
        "risk_resilience": 0,
        "market_context": 0,
        "overall": 0
      },
      "missing_data_count": 0
    }
  ]
}
```

Values above are schema examples, not live market values.

Screen results are sorted by `scores.overall` descending after applying `min_score`.

## Deep mode

### Request

```json
{
  "mode": "deep",
  "ticker": "NVDA"
}
```

Rules:

- `ticker` is required.
- `tickers` must not be supplied.
- Deep mode uses the configured DeepAnalysisProvider.

### Response

```json
{
  "mode": "deep",
  "ticker": "NVDA",
  "metrics": {},
  "scores": {},
  "missing_data": [],
  "analysis": {
    "thesis": "...",
    "positives": ["..."],
    "concerns": ["..."],
    "bull_case": ["..."],
    "bear_case": ["..."],
    "risks": ["..."],
    "what_would_change_view": ["..."],
    "verdict": "...",
    "confidence": "medium"
  },
  "model": "gemini-2.5-flash",
  "disclaimer": "For research purposes only. Not financial advice."
}
```

## Health

`GET /health`

```json
{
  "status": "ok",
  "service": "warren"
}
```

## HTTP status behavior

- `200`: successful Screen or Deep result.
- `422`: invalid request shape (Pydantic/FastAPI validation).
- `502`: upstream market-data or Deep-analysis execution failure.
- `503`: Deep mode requested without valid LLM/provider configuration.

## Compatibility policy

The `/v1` response contract should remain backward compatible. Additive fields may be introduced without a version bump. Removing/renaming fields or changing score meanings materially should result in a new API version or documented migration.

## Recommended future endpoints

Do not add these until needed by a client:

- `GET /v1/methodology` for machine-readable methodology/version metadata.
- `GET /v1/analysis/{ticker}` for cached analysis retrieval.
- `POST /v1/screen` and `POST /v1/deep` only if separate endpoints materially simplify client use; the current mode contract is intentionally compact.
