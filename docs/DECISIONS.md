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

## D-015: Evidence is acquired centrally before agent interpretation

**Decision:** Warren Deep should evolve toward a centralized Evidence Router that acquires heterogeneous evidence before Fundamental, Technical, News/Sentiment, Bull, Bear, Risk or Final roles reason over it.

**Reason:** evidence acquisition and interpretation are different jobs. Central acquisition makes provenance, caching, evaluation and source coverage inspectable while reducing repeated retrieval by multiple agents.

## D-016: Deduplicate events and claims before debate

**Decision:** multiple articles, feeds or social posts referring to the same underlying event should not automatically count as independent corroboration. Warren should normalize them into an evidence claim/event with the original source, independent confirmations and secondary/syndicated mentions preserved separately.

**Reason:** syndicated coverage can create false evidence weight. Five copies of the same Reuters or company-release story are not five independent facts.

## D-017: Source authority and retrieval depth are separate dimensions

**Decision:** Warren should maintain an explicit source hierarchy while also tracking what content was actually retrieved. Primary filings/releases should generally outrank secondary reporting for factual claims, while lower-tier sources can remain highly relevant for sentiment or emerging narratives.

**Reason:** source reputation alone does not justify claims about content Warren has not seen, and different source types answer different research questions.

## D-018: Deterministic financial computation stays outside LLM reasoning

**Decision:** ratios, growth rates, margins, technical indicators, scores, DCF calculations, sensitivity analysis and other reproducible financial calculations should be computed deterministically wherever practical. LLMs interpret and challenge those outputs rather than inventing the numbers.

**Reason:** deterministic computation improves repeatability, testing, numerical reliability, methodology versioning and cost control.

## D-019: Competing agents should reason over the same normalized evidence

**Decision:** Bull, Bear and Risk roles should normally receive the same normalized evidence packet and deterministic calculations before producing independent interpretations.

**Reason:** disagreement should primarily reflect interpretation, assumptions and risk appetite rather than inconsistent fact collection. Shared evidence also makes factual contradictions between agents easier to detect and evaluate.

## D-020: End-user research value comes before provider minimization

**Decision:** Warren may combine primary sources, structured providers, web/news discovery and social/sentiment sources when doing so materially improves coverage or uncertainty reduction. The goal is not to minimize the number of sources; it is to maximize useful, independent evidence at sustainable cost.

**Reason:** broad coverage can improve research completeness, but integrations should be selected for incremental user value rather than source count alone.

## D-021: Evidence acquisition should be cost-aware

**Decision:** the Evidence Router should eventually support an evidence budget per analysis. Prefer free authoritative sources first, use structured/paid providers where they materially reduce engineering effort or uncertainty, and escalate to premium/on-demand evidence only when it can change the quality of the conclusion.

**Reason:** a public research product must optimize both user value and unit economics. Central routing allows Warren to buy the next most useful piece of evidence instead of paying for every possible source on every request.

## D-022: Architectural differentiation is a research hypothesis until validated

**Decision:** Warren may market inspectable architectural properties—source attribution, deterministic calculations, explicit evidence gaps, shared evidence and thesis-change conditions—but must not claim superior accuracy, returns, factuality or cost versus TradingAgents or other systems until controlled evaluation demonstrates it.

**Reason:** separating product narrative from empirical claims preserves credibility and creates a clear research agenda. See `DIFFERENTIATION_RESEARCH_THESIS.md`.
