# Changelog

All notable product/module changes should be recorded here.

## Unreleased

### Added

- Warren reusable stock-intelligence package.
- `screen` mode for deterministic, LLM-free universe ranking.
- `deep` mode for one-company Bull/Bear/Risk/final synthesis.
- Replaceable `MarketDataProvider` and `DeepAnalysisProvider` interfaces.
- Yahoo Finance development adapter.
- Gemini deep-analysis adapter.
- FastAPI `/v1/analyze` adapter.
- Offline engine and API-contract tests.
- GitHub Actions test workflow.
- Product, architecture, API, methodology, integration, evaluation, risk, roadmap, security and naming documentation.

### Known limitations

- scoring thresholds/weights are not yet calibrated as predictive investment signals;
- Deep mode does not yet ingest verified filings/news/macro/estimate-revision evidence;
- Yahoo Finance is a development data source rather than a production SLA-backed feed;
- Warren is an internal working name pending legal trademark clearance.
