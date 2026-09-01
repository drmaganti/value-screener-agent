# Roadmap

## v0.2 — Reusable core (current)

- [x] Warren package boundary independent of client applications.
- [x] Screen and Deep modes.
- [x] Provider protocols.
- [x] Yahoo Finance development data adapter.
- [x] Deterministic category scoring.
- [x] TradingAgents-inspired Bull/Bear/Risk -> Final Deep flow.
- [x] Gemini deep-analysis provider.
- [x] FastAPI adapter.
- [x] Product, architecture, API and methodology documentation.
- [ ] Unit/contract test baseline.
- [ ] CI workflow.

## v0.3 — Evidence quality

Goal: make Deep mode materially more complete without letting LLMs invent context.

- filings/earnings evidence provider;
- current news provider;
- macro/industry context provider;
- evidence IDs/citations passed through Deep output;
- data freshness metadata;
- claim-level evidence checks;
- structured company/filing evidence bundle.

Target Deep architecture:

```text
Fundamentals / filings
Valuation
Business quality / growth
News / macro
Market context
Estimate revisions
        |
Bull + Bear + Risk
        |
Final evaluator
```

## v0.4 — Better Screen methodology

- sector-relative valuation;
- company-history-relative valuation;
- ROIC;
- multi-year revenue/EPS/FCF growth;
- dilution/share-count trend;
- margin trend/stability;
- interest coverage;
- analyst estimate revision breadth/magnitude;
- earnings surprise/revision signals;
- methodology version in every output.

## v0.5 — Evaluation and calibration

- frozen point-in-time datasets;
- score-decile backtests;
- 1m/3m/6m/12m benchmark-relative outcomes;
- factor ablations;
- sector/regime analysis;
- Deep factuality eval suite;
- Bull/Bear/Risk ablation versus single-agent baseline;
- confidence calibration.

## v0.6 — Cost, caching and reliability

- cached market snapshots;
- cached fundamentals until material update;
- Deep cache keyed to evidence version;
- event-driven invalidation after earnings/filings/material news;
- retries/circuit breakers;
- provider fallback;
- observability for latency, provider errors, token/call cost.

## v0.7 — Production data adapters

Evaluate paid/licensed providers based on coverage, point-in-time history, terms and cost. Candidates may include providers such as FMP, Polygon or other licensed fundamentals/estimate feeds. The provider interface should prevent client changes.

## Integration milestones

### Weekly Value Screen

- preserve existing strategy rules;
- call Warren Screen on strategy survivors;
- compare ranking with current weekly composite;
- run shadow mode before changing published picks;
- call Warren Deep on only the final small set;
- measure incremental usefulness and cost.

### Parse

- define stock detail UX;
- call Deep on explicit user action or selected candidate;
- render company quality separately from valuation;
- show supporting evidence and missing-data confidence.

### Value Screener

- decide which current scoring should remain strategy-specific versus move into Warren;
- avoid double-counting duplicated factors;
- use Warren as shared intelligence rather than forked logic.

## Later possibilities

- compare two stocks using the same evidence schema;
- watchlist change detection;
- thesis monitoring after earnings;
- portfolio-level research summaries;
- pluggable investment styles/weight profiles only after core methodology is validated;
- local/open-source deep-analysis provider for low-cost/private deployments.

## Explicitly deferred

- trade execution;
- autonomous portfolio management;
- personalized allocation advice;
- running Deep on every stock in an index;
- public commercialization under the Warren name before trademark clearance.
