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
- analyst-estimate revisions as a separate signal rather than an implicit valuation input.

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

Deep mode receives the list of missing metrics and is instructed to reduce confidence when evidence is insufficient.

## Deep methodology

Deep mode is inspired by TradingAgents but adapted for fundamental stock research.

### Step 1: verified evidence

The LLM receives structured metrics and deterministic scores. Numerical claims should originate from providers, not model memory.

### Step 2: independent perspectives

Three calls run concurrently:

- Bull analyst: strongest supported positive case and its weaknesses.
- Bear analyst: strongest supported negative case and its weaknesses.
- Risk reviewer: risks, missing evidence and risk summary.

They do not see each other's arguments.

### Step 3: final synthesis

The final evaluator sees:

- original structured evidence;
- deterministic scores;
- Bull output;
- Bear output;
- Risk output.

It is told to synthesize rather than vote and to distinguish business quality from valuation.

## Evidence that is not yet included

Deep mode should not be considered complete until verified additional evidence sources are added, especially:

- SEC/SEDAR+/company filings;
- earnings releases and guidance;
- current news;
- macro/industry context;
- estimate revisions;
- peer/sector comparisons.

Until those exist, prompts explicitly prohibit inventing those facts.

## Methodology versioning

When weights, thresholds or factor definitions change materially, Warren should persist a `methodology_version` with outputs so historical analyses remain interpretable.
