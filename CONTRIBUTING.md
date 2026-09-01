# Contributing

## Development principles

Changes to Warren should preserve three boundaries:

1. client applications do not own Warren methodology;
2. market-data/LLM vendors remain replaceable providers;
3. Screen stays deterministic and LLM-free unless a future version explicitly changes that contract.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## Pull requests

A change that alters scoring, evidence inputs or Deep prompts should include:

- tests;
- methodology/documentation changes;
- rationale for the change;
- expected impact on compatibility/cost;
- an evaluation plan when output behavior changes materially.

## Methodology changes

Do not silently change score definitions or weights. Material changes should:

- update `docs/METHODOLOGY.md`;
- receive a methodology version once versioning is implemented;
- include regression/calibration evidence before being described as an improvement.

## Provider additions

New market-data providers should return `MetricSnapshot` and avoid leaking provider-specific shapes into callers.

New Deep providers should return the same validated `DeepAnalysis` contract.

## Financial claims

Do not add hard-coded claims about specific companies to prompts or tests except frozen evaluation fixtures. Numerical facts should originate from provider/evidence inputs.

## Secrets

Never commit API keys. See `SECURITY.md`.
