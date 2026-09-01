# Product Definition

## Vision

Warren is a reusable stock-intelligence capability that helps software products answer two different questions efficiently:

1. **Screen:** Which companies in a universe deserve more research?
2. **Deep:** For one company, what is the strongest evidence for and against the investment thesis?

The engine should be reusable from Parse, Value Screener, scheduled workflows and future products without duplicating stock-analysis logic.

## Product principles

1. **Facts before interpretation.** Prices, ratios and financial metrics come from data providers. LLMs interpret evidence; they do not manufacture financial facts.
2. **Company quality is not stock attractiveness.** A great business can be an expensive investment.
3. **Challenge the thesis.** Deep analysis must include independent bull, bear and risk perspectives.
4. **Spend AI only where it adds value.** Screening is deterministic. Multi-agent reasoning is reserved for selected companies.
5. **Explain the result.** Users should understand positives, concerns, risks and what would change the view.
6. **Provider independence.** Market-data and LLM vendors are adapters, not the product architecture.
7. **No false precision.** Missing evidence reduces confidence rather than being silently inferred.

## Primary users

### Product integrations

- Parse: deep analysis after a user identifies a company.
- Value Screener: general ranking after strategy-specific filtering.
- Weekly Value Screen: strategy funnel -> Warren screen -> optional Warren deep on finalists.
- Future watchlist, portfolio or research products.

### End-user jobs

- Rank many companies without paying for an AI analysis on each one.
- Understand why a stock scored well or poorly.
- Compare business quality with valuation.
- See the strongest bull and bear cases.
- Identify material risks and missing evidence.
- Know what facts would change the conclusion.

## Modes

### Screen mode

**Input:** caller-supplied ticker universe plus result limits/thresholds.

**Output:** ranked companies with category and overall scores.

**Expected characteristics:**

- low cost;
- no LLM call;
- usable on hundreds of companies;
- deterministic for the same data snapshot;
- suitable as a component inside another strategy.

Screen is intentionally **not an investment strategy**. A calling product can apply its own rules before or after Warren.

### Deep mode

**Input:** one ticker.

**Output:** structured evidence, scores, bull case, bear case, risk review, final thesis, verdict and confidence.

**Expected characteristics:**

- more expensive than screen;
- independent reasoning roles;
- evidence-bound prompts;
- explicit missing-data handling;
- suitable for user-requested company research or a small number of finalists.

## Non-goals

Warren does not currently:

- execute trades;
- manage portfolios;
- provide personalized suitability advice;
- guarantee future returns;
- replace licensed financial advice;
- run full multi-agent analysis across an index;
- maintain index constituent lists as part of the core engine;
- define the Weekly Value Screen strategy itself.

## Success metrics

### Product metrics

- Screen latency per 100/500 symbols.
- Deep-analysis latency and cost per company.
- Cache hit rate once caching is implemented.
- Percentage of analyses with sufficient source coverage.

### Quality metrics

- Deterministic scoring regression pass rate.
- Factual error / unsupported-claim rate in Deep outputs.
- Bull/bear argument diversity.
- Risk-recall rate against a labeled evaluation set.
- Score calibration against future benchmark-relative returns.
- User-rated usefulness/explainability.

## Current maturity

The present implementation establishes the reusable module boundaries and initial methodology. The scoring thresholds are heuristics and are not yet empirically calibrated as a return-prediction model. See `METHODOLOGY.md` and `ROADMAP.md`.
