# Architecture / Product Decisions

This file records decisions that should not be rediscovered each time Warren is integrated into a new product.

## D-001: Warren is a standalone capability

**Decision:** stock intelligence lives in a reusable module/service rather than inside Parse or Value Screener.

**Reason:** one methodology, one evaluation surface, one place to improve data/providers/prompts.

## D-002: Two modes, two jobs

**Decision:** Warren exposes `screen` and `deep`.

- Screen finds/ranks companies from a caller-supplied universe.
- Deep investigates one company.

**Reason:** index-scale multi-agent analysis is unnecessarily expensive and slow.

## D-003: Screen requires a universe, not a ticker

**Decision:** Screen receives `tickers`; Deep receives `ticker`.

**Reason:** Screen and Deep are conceptually different jobs and should not overload a single-stock input.

## D-004: Screen is not the Weekly Value Screen strategy

**Decision:** Weekly Value Screen retains strategy-specific logic (pullback, RSI, earnings blackout, repeat-pick rules, catalyst strategy). Warren Screen provides general company ranking.

**Reason:** the shared module must be useful to strategies/products that do not share a contrarian-value thesis.

## D-005: Keep TradingAgents' challenge architecture in Deep

**Decision:** Deep uses independent Bull, Bear and Risk roles followed by final synthesis.

**Reason:** competing interpretations are more useful than a single unchallenged LLM narrative.

## D-006: Facts come from providers

**Decision:** LLMs do not generate source-of-truth prices/ratios/fundamentals.

**Reason:** financial hallucinations are unacceptable and unnecessary when structured sources exist.

## D-007: Provider independence

**Decision:** Yahoo, SEC, FRED and Gemini are adapters behind protocols.

**Reason:** data licensing, cost, model quality and vendor availability will change.

## D-008: Caller owns universe membership

**Decision:** the Warren core does not own S&P 500/TSX 60/etc. membership.

**Reason:** universe definitions can be strategy/product-specific and become stale. Callers may pass named-universe results once a separate universe service exists.

## D-009: Business quality and valuation remain separate

**Decision:** Deep and Screen should not collapse these concepts into one opaque judgment.

**Reason:** an excellent company can be an unattractive investment at a sufficiently high price.

## D-010: `Warren` is a working name, not a cleared public brand

**Decision:** use Warren internally while trademark clearance remains incomplete.

**Reason:** preliminary searches identified historically/currently relevant financial/software marks. See `NAMING.md`.

## D-011: Deep evidence is explicit and source-attributed

**Decision:** Deep receives a typed `EvidenceBundle` collected before LLM reasoning. The same packet is passed to Bull, Bear, Risk and Final and returned to the caller.

**Reason:** users and evals need to know what information the model actually had. Provenance must not exist only inside a prompt.

## D-012: Retrieval depth limits what the model may claim

**Decision:** Warren treats filing metadata as filing metadata and news headlines as headlines. A high-authority source does not authorize the model to infer content that was not retrieved.

**Reason:** claiming unseen filing/article contents is a hallucination even when the referenced source itself is reputable.

## D-013: Partial evidence failure degrades confidence, not the entire request

**Decision:** independent evidence providers report `ok`, `partial`, `unavailable` or `error`. Deep continues with remaining evidence unless the core market-data or DeepAnalysisProvider fails.

**Reason:** filings, news, estimates and macro sources have different availability and failure modes. All-or-nothing retrieval would make Warren unnecessarily brittle and hide useful partial evidence.

## D-014: Estimate revisions are Deep evidence before they become a Screen factor

**Decision:** v0.3 exposes estimate trends/revisions to Deep but does not change deterministic Screen weights.

**Reason:** adding a factor to Screen is a methodology change and should be supported by point-in-time calibration/backtesting rather than architectural enthusiasm alone.
