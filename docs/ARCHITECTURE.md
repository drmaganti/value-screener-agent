# Architecture

## System boundary

Warren is a domain module with optional delivery adapters. Client products should depend on Warren's public methods or HTTP contract, not on Yahoo Finance or Gemini directly.

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
           +-------------+-------------+
           |                           |
   MarketDataProvider          DeepAnalysisProvider
           |                           |
     Yahoo today                 Gemini today
     paid feed later             other model later
```

## Core components

### `warren.engine.Warren`

Owns orchestration and the stable public behaviors:

- `screen(tickers, top_n, min_score)`
- `deep(ticker)`

The engine does not know which application called it.

### `MarketDataProvider`

A protocol for obtaining a verified `MetricSnapshot`. The initial adapter is `YFinanceMarketDataProvider`.

A production provider can later use licensed data without changing callers.

### Deterministic scoring

`warren.scoring.score_metrics` transforms structured metrics into category scores. This stage is LLM-free and is shared by both modes.

### `DeepAnalysisProvider`

A protocol for the expensive interpretation stage. The initial Gemini implementation uses the TradingAgents pattern we deliberately chose:

```text
Structured evidence + deterministic scores
                 |
      +----------+----------+
      |          |          |
     Bull       Bear       Risk
      |          |          |
      +----------+----------+
                 |
          Final synthesis
```

Bull, Bear and Risk run independently and concurrently. The final evaluator receives all three outputs plus the original structured evidence.

## Why this differs from TradingAgents

We preserve its strongest architectural principles but remove trading-specific complexity that is not needed for Warren.

Preserved:

- specialized roles;
- bull vs. bear challenge;
- independent risk review;
- final synthesis;
- data as source of truth rather than LLM-generated numbers.

Simplified/removed for now:

- trader/portfolio-manager execution roles;
- aggressive/neutral/conservative portfolio agents;
- multi-agent execution for every screened stock;
- checkpointing/trading state.

Planned evidence agents include filings/fundamentals, verified news/macro, market context and estimate revisions. See `ROADMAP.md`.

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

No DeepAnalysisProvider is invoked.

### Deep

```text
single ticker
      |
market data
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

- Screen: structured data calls + local calculations.
- Deep: structured data calls + 4 LLM requests today (Bull, Bear, Risk concurrently; Final afterward).
- Future caching should separately cache data snapshots, evidence summaries and final analyses because they have different freshness requirements.

## Freshness model (target)

Different evidence should have different TTL/event refresh policies:

- price/market context: short TTL;
- fundamentals: refresh on filings/earnings or daily provider update;
- news: short TTL/event-driven;
- business description: long TTL;
- Deep synthesis: invalidated by material evidence changes.

## Failure behavior

- A failed ticker in Screen should not fail the entire batch.
- Deep should fail visibly if verified evidence cannot be fetched.
- Missing metrics are returned explicitly.
- Deep mode requires a configured deep-analysis provider.
- LLM output must be validated against structured schemas before returning to clients.
