# Methodology

## Important status

The current scoring model is an **initial heuristic model**, not a validated return-prediction system. It exists to establish explainable, deterministic behavior and a stable interface. Thresholds and weights must be calibrated with historical/out-of-sample evaluation before they are treated as investment signals.

## Category scores

Warren currently reports six category scores, each from 0 to 100:

1. Fundamentals
2. Valuation
3. Business quality
4. Growth
5. Risk resilience
6. Market context

The current overall score is:

```text
Fundamentals      30%
Valuation         25%
Business quality  20%
Growth            10%
Risk resilience   10%
Market context     5%
```

This weighting reflects a long-term fundamental research orientation rather than a short-term trading model.

## Fundamentals

Initial inputs include:

- positive free cash flow;
- positive operating cash flow;
- current ratio;
- debt-to-equity;
- profit margin.

## Valuation

Initial inputs include:

- trailing P/E;
- forward P/E;
- PEG;
- EV/EBITDA;
- free-cash-flow yield.

Current absolute bands are placeholders. Planned improvements include:

- sector-relative valuation;
- company-history-relative valuation;
- earnings/FCF normalization;
- capital-intensity-aware metrics;
- analyst-estimate revisions as a separate Screen signal rather than an implicit valuation input.

## Business quality

Initial inputs include:

- ROE;
- ROA;
- gross margin;
- operating margin;
- positive free cash flow.

Planned improvements include ROIC, margin stability/trend, dilution, capital allocation, recurring/repeat revenue proxies and competitive-position evidence.

## Growth

Initial inputs:

- revenue growth;
- earnings growth.

Planned improvements include multi-year CAGR, forward consensus, estimate-revision breadth/magnitude and growth quality.

## Risk resilience

Initial inputs:

- beta;
- debt-to-equity;
- current ratio;
- positive free cash flow.

This is not a complete investment-risk model. Planned additions include interest coverage, refinancing maturity, customer concentration, cyclicality, dilution, accounting flags and event/regulatory risks.

## Market context

Market context is deliberately low weight. Initial inputs compare price with the 200-day average and 52-week high.

Technical context should not turn a weak business into a high-quality investment. Strategy-specific technical rules belong in calling strategies such as Weekly Value Screen.

## Missing data

Warren does not replace missing metrics with invented values. Category averages use available components; if no component is available the current neutral fallback is 50.

Deep mode receives the list of missing metrics plus evidence-source availability and is instructed to reduce confidence when evidence is insufficient.

## Deep methodology

Deep mode is inspired by TradingAgents but adapted for fundamental stock research.

### Step 1: structured company metrics

Warren retrieves a `MetricSnapshot` and computes deterministic category scores. Numerical company metrics originate from the configured market-data provider, not model memory.

### Step 2: source-attributed evidence packet

v0.3 adds an explicit `EvidenceBundle` before any LLM reasoning.

Current evidence sources:

- **SEC EDGAR:** recent material filing metadata (`10-K`, `10-Q`, `8-K`, `20-F`, `40-F`, `6-K` and amendments) for exact US ticker mappings;
- **Yahoo Finance/yfinance:** recent news headlines;
- **Yahoo Finance/yfinance:** EPS estimate trend/revision counts and forward earnings/revenue growth fields when available;
- **Yahoo Finance/yfinance:** recent actual-vs-estimate earnings history;
- **FRED:** selected macro observations when `FRED_API_KEY` is configured.

Every provider reports an explicit source status. One failed source does not cause the other evidence to disappear.

### Step 3: evidence-depth rules

Warren distinguishes the authority of a source from the depth actually retrieved:

- SEC filing metadata proves that a filing/form/date exists; it does **not** prove the contents of that filing were read.
- A Yahoo headline is headline-level evidence; the model may not infer the unseen article body.
- Structured estimate revisions, earnings-history fields and FRED observations may be directly compared as supplied values.
- Missing/unavailable sources should lower confidence instead of being filled from model memory.

These restrictions are embedded in the Deep prompts.

### Step 4: independent perspectives

Three calls run concurrently:

- Bull analyst: strongest supported positive case and its weaknesses.
- Bear analyst: strongest supported negative case and its weaknesses.
- Risk reviewer: risks, missing evidence, stale/incomplete-source concerns and risk summary.

They do not see each other's arguments.

### Step 5: final synthesis

The final evaluator sees:

- original structured metrics;
- deterministic scores;
- the exact source-attributed evidence packet;
- Bull output;
- Bear output;
- Risk output.

It is told to synthesize rather than vote, weight source facts above agent rhetoric, distinguish business quality from valuation, and reduce confidence when important evidence is missing.

## Evidence still not included

v0.3 materially improves grounding but Deep should still not be considered complete. Important missing areas include:

- actual SEC filing text/XBRL facts and management commentary rather than metadata alone;
- SEDAR+ / Canadian issuer filing evidence;
- earnings-release and guidance text;
- full licensed news/article content;
- industry/peer context;
- point-in-time historical estimates;
- explicit evidence IDs/citations at individual generated-claim level.

## Estimate revisions and Screen

Estimate revisions are currently **Deep evidence only**. They are not yet part of the deterministic Screen score. Adding them to Screen belongs in a methodology change that is backtested/calibrated rather than silently changing the current score.

## Macro scope

The initial FRED bundle is intentionally small and generic (rates, unemployment, CPI context). Macro relevance varies materially by company and sector. Warren should not give generic macro signals large deterministic weight until sector/company sensitivity is validated.

## Methodology versioning

When weights, thresholds or factor definitions change materially, Warren should persist a `methodology_version` with outputs so historical analyses remain interpretable.
