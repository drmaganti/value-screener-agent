# Evaluation Strategy

Warren should be evaluated as both a deterministic scoring system and an evidence-grounded AI research system.

## 1. Deterministic scoring tests

Required regression coverage:

- score boundaries remain 0-100;
- same input snapshot produces same scores;
- missing metrics never produce exceptions;
- positive cash flow is treated consistently;
- higher debt does not improve risk resilience;
- lower valuation multiples do not reduce valuation score inside comparable bands;
- overall weights sum to 100%;
- Screen ordering is descending by overall score;
- failed tickers do not fail a Screen batch.

## 2. Contract tests

- Screen requires `tickers` and rejects single `ticker`.
- Deep requires `ticker` and rejects `tickers`.
- response schemas validate;
- `/v1` compatibility is preserved;
- provider implementations satisfy domain models.

## 3. Deep-analysis factuality eval

Build a labeled set of companies and frozen evidence packets. For each model/version measure:

- unsupported numerical claim rate;
- unsupported company/event claim rate;
- use of evidence actually present in the packet;
- appropriate acknowledgement of missing evidence;
- schema-valid output rate;
- repeated-run consistency.

Target: unsupported numerical claims should be effectively zero because prompts provide structured source-of-truth metrics and prohibit invention.

## 4. Debate-quality eval

Measure whether Bull/Bear/Risk actually add distinct value:

- overlap between Bull and Bear arguments;
- whether Bear identifies material downside absent from Bull;
- whether Risk identifies evidence gaps;
- whether Final synthesis reflects both sides rather than simply repeating Bull;
- whether confidence falls when important evidence is removed.

Ablation test: compare single-agent final analysis against the full Bull/Bear/Risk architecture on the same evidence set.

## 5. Scoring calibration / investment-outcome evaluation

Do not optimize against an in-sample historical dataset and then call it predictive.

Recommended approach:

1. Freeze methodology version.
2. Generate historical point-in-time scores using data available at that date.
3. Measure forward 1m/3m/6m/12m benchmark-relative returns.
4. Split by sector, market regime and market cap.
5. Validate on out-of-sample periods.
6. Compare score deciles rather than only top picks.
7. Track turnover and survivorship bias.

Questions to answer:

- Do higher overall scores correspond to better forward outcomes?
- Which category is actually predictive?
- Does valuation improve outcomes conditional on quality?
- Are estimate revisions additive?
- Is market context useful at its current 5% weight?

## 6. Product evaluation

For user-facing integrations measure:

- % of Screen users who open Deep;
- Deep usefulness rating;
- time-to-understanding versus existing research workflow;
- user clicks into supporting evidence;
- repeated usage;
- cost per completed useful analysis.

## 7. Release gates

Before calling a methodology production-ready:

- deterministic tests pass;
- no known P0 factuality failures;
- model/schema validation pass rate meets target;
- methodology has an explicit version;
- point-in-time evaluation methodology is documented;
- major data-provider limitations are disclosed.

## 8. Evaluation artifacts

Recommended repository structure:

```text
tests/                 deterministic/unit/contract tests
evals/
  fixtures/            frozen evidence packets
  labels/              expected risk/factuality annotations
  deep_factuality.py
  debate_ablation.py
  score_calibration.py
```

Evaluation data should avoid using future information when assessing historical decisions.
