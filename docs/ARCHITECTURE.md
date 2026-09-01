# Architecture

## System boundary

Warren is a domain module with optional delivery adapters. Client products should depend on Warren's public methods or HTTP contract, not on Yahoo Finance, SEC, FRED or Gemini directly.

```text
Client products
(Parse / Value Screener / weekly workflow / future app)
                         |
               +---------+---------+
               |                   |
         Python package          HTTP API
               |                   |
               +---------+---------+
                         |
                    Warren engine
                         |
       +-----------------+------------------+
       |                 |                  |
MarketDataProvider  EvidenceProvider  DeepAnalysisProvider
       |                 |                  |
 Yahoo today       Composite today      Gemini today
 paid later        |-- SEC filings      other model later
                   |-- Yahoo evidence
                   `-- FRED macro
```

## Core components

### `warren.engine.Warren`

Owns orchestration and the stable public behaviors:

- `screen(tickers, top_n, min_score)`
- `deep(ticker)`

The engine does not know which application called it.

### `MarketDataProvider`

A protocol for obtaining a structured `MetricSnapshot`. The initial adapter is `YFinanceMarketDataProvider`.

A production provider can later use licensed data without changing callers.

### Deterministic scoring

`warren.scoring.score_metrics` transforms structured metrics into category scores. This stage is LLM-free and is shared by both modes.

### `EvidenceProvider`

A protocol for collecting source-attributed context used only by Deep.

The initial `CompositeEvidenceProvider` merges independent providers and isolates failures. One unavailable source does not erase evidence from the others.

Current providers:

- `SecFilingEvidenceProvider` — recent SEC filing metadata from official SEC endpoints;
- `YahooEvidenceProvider` — recent headlines, EPS/revenue estimates and revisions, and recent earnings surprise history;
- `FredMacroEvidenceProvider` — optional macro observations when `FRED_API_KEY` is configured.

The evidence packet also carries `source_status` entries (`ok`, `partial`, `unavailable`, `error`) so the model and client can reason about evidence quality explicitly.

### `DeepAnalysisProvider`

A protocol for the expensive interpretation stage. The initial Gemini implementation uses the TradingAgents pattern we deliberately chose:

```text
Metrics + scores + source-attributed evidence
                    |
          +---------+---------+
          |         |         |
         Bull      Bear      Risk
          |         |         |
          +---------+---------+
                    |
             Final synthesis
```

Bull, Bear and Risk run independently and concurrently. The final evaluator receives all three outputs plus the original source packet and is instructed to weight source facts above agent rhetoric.

## Evidence semantics

The architecture distinguishes **retrieval depth** from **source authority**.

- SEC is authoritative, but v0.3 retrieves filing metadata rather than the filing body. Therefore the model may say a filing exists, but not what the filing says.
- Yahoo news provides current headline-level context. A headline is evidence of a reported claim/topic, not proof of all underlying facts.
- Yahoo estimate/revision tables and earnings history are structured data and can be compared directly.
- FRED observations are structured macro values from a public economic-data source.

This distinction is enforced in Deep prompts and should eventually be tested with claim-level factuality evals.

## Why this differs from TradingAgents

We preserve its strongest architectural principles but remove trading-specific complexity that is not needed for Warren.

Preserved:

- specialized roles;
- bull vs. bear challenge;
- independent risk review;
- final synthesis;
- data/evidence as source of truth rather than LLM-generated numbers.

Simplified/removed for now:

- trader/portfolio-manager execution roles;
- aggressive/neutral/conservative portfolio agents;
- multi-agent execution for every screened stock;
- checkpointing/trading state.

Instead of adding an LLM agent for every evidence category, v0.3 first makes the evidence packet explicit and source-attributed. Dedicated evidence-analysis agents can be added later only if evals show they improve quality enough to justify extra latency/cost.

## Mode boundaries

### Screen

```text
caller universe
      |
market data
      |
deterministic scoring
      |
filter + rank
```

No EvidenceProvider or DeepAnalysisProvider is invoked.

### Deep

```text
single ticker
      |
market data + evidence collection
      |
deterministic scoring
      |
independent bull/bear/risk reasoning
      |
final synthesis
```

## Strategy separation

Warren Screen is not the Weekly Value Screen strategy.

A strategy can wrap Warren:

```text
Weekly strategy rules
(pullback, RSI, earnings blackout, prior-pick exclusion, catalyst rules)
                         |
                    survivors
                         |
                   Warren Screen
                         |
                    finalists
                         |
                    Warren Deep
```

This allows other strategies to use the same intelligence engine without inheriting Weekly Value Screen assumptions.

## Dependency direction

Desired dependency direction:

```text
API/UI -> Warren -> provider protocols <- provider implementations
```

Never:

```text
Warren -> Parse
Warren -> Value Screener
Warren -> a specific UI
```

## Cost architecture

- Screen: structured market-data calls + local calculations.
- Deep: market-data call + evidence-source network calls + 4 LLM requests today (Bull, Bear, Risk concurrently; Final afterward).
- FRED is optional and adds no LLM call.
- Future caching should separately cache market snapshots, filings/news/estimate evidence, macro evidence and final analyses because they have different freshness requirements.

## Freshness model (target)

Different evidence should have different TTL/event refresh policies:

- price/market context: short TTL;
- fundamentals: refresh on filings/earnings or provider update;
- filing metadata: event-driven / daily check;
- news: short TTL/event-driven;
- estimate revisions: daily or after provider update;
- macro: based on series release frequency;
- Deep synthesis: invalidated by material evidence changes.

v0.3 does not yet implement persistent caching/freshness metadata beyond source dates supplied by individual evidence items.

## Failure behavior

- A failed ticker in Screen does not fail the entire batch.
- Evidence-provider failures in Deep are recorded in `source_status` and the remaining evidence continues.
- Deep synthesis fails visibly if the DeepAnalysisProvider itself cannot run.
- Missing metrics are returned explicitly.
- Deep mode requires a configured deep-analysis provider.
- LLM output must be validated against structured schemas before returning to clients.
