# Risks and Limitations

## Product risk

A numerical score can create more confidence than the underlying evidence deserves. Warren must make category scores explainable and distinguish heuristic ranking from validated prediction.

## Data risk

The initial Yahoo Finance adapter is useful for development but is not a guaranteed institutional-grade source.

Risks include:

- missing fields;
- inconsistent field availability across markets;
- provider throttling;
- delayed/restated fundamentals;
- ambiguous units;
- changes to unofficial provider behavior.

Mitigation: keep `MarketDataProvider` replaceable and expose missing data.

## Methodology risk

Current score bands/weights are heuristics. They have not yet demonstrated out-of-sample predictive power.

Mitigation:

- methodology versioning;
- point-in-time backtesting;
- factor-level evaluation;
- sector/regime analysis;
- avoid marketing score precision as proven alpha.

## LLM factuality risk

Deep analysis can hallucinate unsupported context.

Mitigation already present:

- verified structured metrics are supplied directly;
- Bull/Bear/Risk are instructed to use only supplied evidence;
- the final evaluator receives the same source evidence;
- output is schema validated;
- missing evidence must reduce confidence.

Future mitigation:

- source citations/evidence IDs;
- filings/news retrieval;
- claim-level verification;
- evaluation gates.

## Multi-agent failure modes

Multiple agents do not automatically create correctness. They can share the same model biases or amplify a weak premise.

Mitigation:

- independent prompts;
- original evidence supplied to every role;
- final synthesis rather than majority vote;
- ablation testing against a single-agent baseline;
- eventually use independent models selectively if evidence shows benefit.

## Cost risk

Deep mode currently requires four LLM calls per company. Running it across an index would be wasteful.

Mitigation:

- Screen is LLM-free;
- Deep is one-stock-at-a-time;
- call Deep only on user request/finalists;
- add caching and event-driven invalidation.

## Regulatory / communications risk

Warren is financial research software. Public-facing implementations must avoid presenting outputs as personalized investment advice unless the operating product has appropriate legal/compliance review.

The product should:

- label research limitations;
- avoid guaranteed-return language;
- avoid pretending a score is certainty;
- retain evidence and methodology versions where practical;
- seek legal advice before material public commercialization in regulated contexts.

## Naming / trademark risk

`Warren` is currently an internal/product-development name and has **not been legally cleared for public commercial use**. See `NAMING.md`.

## Operational risk

- provider outage can block Deep;
- partial Screen data can alter rankings;
- model changes can alter Deep outputs;
- secrets must not be logged or committed;
- external API latency can cause timeouts.

## Security/privacy risk

Warren currently processes public market data and tickers, so personal-data exposure is low. Future portfolio/watchlist integrations could introduce sensitive user financial information. The core engine should not require user identity or holdings unless a future feature explicitly needs them.
