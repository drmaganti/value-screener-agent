# Changelog

All notable product/module changes should be recorded here.

## Unreleased / v0.3.0

### Added

- Reusable `EvidenceProvider` protocol and typed `EvidenceBundle`.
- `CompositeEvidenceProvider` with per-source failure isolation.
- Official SEC EDGAR recent filing metadata provider for exact US ticker mappings.
- Yahoo/yfinance recent headline evidence.
- Yahoo/yfinance EPS trend and revision-count evidence.
- Yahoo/yfinance forward earnings/revenue growth estimate fields and recent earnings surprise history.
- Optional FRED macro evidence with explicit unavailable state when `FRED_API_KEY` is absent.
- Deep API response now returns the exact evidence packet used for synthesis.
- Deep prompts explicitly prevent inference of filing contents from metadata and article contents from headlines.
- Evidence-provider resilience tests.
- Data-source documentation and v0.3 methodology/evaluation updates.

### Changed

- `DeepAnalysisProvider.analyze` now receives `EvidenceBundle` in addition to metrics and deterministic scores.
- Warren Deep gathers evidence before Bull/Bear/Risk synthesis.
- Evidence source failures degrade gracefully and are returned through `source_status` rather than automatically failing Deep.
- API/package version advanced to `0.3.0`.

### Known limitations

- scoring thresholds/weights are not yet calibrated as predictive investment signals;
- SEC evidence is filing metadata, not filing-content extraction;
- Yahoo news evidence is headline-level, not full-article retrieval;
- Canadian SEDAR+ filing evidence is not yet implemented;
- FRED context is optional and generic/US-centric;
- Yahoo Finance is a development data source rather than a production SLA-backed feed;
- Warren is an internal working name pending legal trademark clearance.

## v0.2.0

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
