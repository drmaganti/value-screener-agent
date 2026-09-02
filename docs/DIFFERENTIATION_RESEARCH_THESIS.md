# Warren Differentiation / Research Thesis

## Purpose

This document captures the design thesis behind Warren and the reasons its architecture may be better suited to a production investment-research product than a direct reproduction of a tool-driven multi-agent research system such as TradingAgents.

It is intentionally written for reuse in three contexts:

1. **Product/marketing:** explain why Warren is trustworthy and useful without making unvalidated performance claims.
2. **Technical writing:** explain the architectural choices and trade-offs.
3. **Research paper:** define testable hypotheses and an evaluation plan for comparing Warren with alternative agent architectures.

> **Claim discipline:** Warren should not publicly claim to be more accurate, more profitable, or better than TradingAgents or another system until controlled evaluation supports that claim. The architectural advantages below are design hypotheses unless explicitly demonstrated by evidence.

---

## 1. Core thesis

Multi-agent debate is valuable, but the quality of the debate is bounded by the quality, independence, provenance and interpretation of the evidence supplied to the agents.

A direct tool-driven multi-agent architecture often looks like:

```text
Analyst agent
    |
Tools / APIs / web search
    |
Agent interpretation
    |
Debate / decision
```

Warren inserts an explicit evidence and calculation layer before agent interpretation:

```text
Primary sources + structured APIs + web/news discovery
                         |
                  Evidence Router
                         |
        normalize / deduplicate / corroborate
                         |
                   Evidence Claims
                         |
          deterministic calculations
                         |
 Fundamental / Technical / News / Sentiment analysts
                         |
                   Bull <-> Bear
                         |
                    Risk review
                         |
                  Warren evaluator
                         |
           Attractive / Watch / Avoid
```

The central hypothesis is:

> **Acquire facts once, preserve their provenance, reason over normalized evidence many times.**

This separates evidence acquisition from interpretation while retaining the strongest feature of TradingAgents: specialized perspectives and adversarial challenge.

---

## 2. How Warren differs from the paper architecture

### TradingAgents-style approach

The TradingAgents architecture gives specialized agents access to tools appropriate to their roles. Fundamental, technical, sentiment and news analysts retrieve and analyze information; Bull and Bear researchers debate; risk roles challenge the recommendation; and a final decision-maker synthesizes the result.

The architecture's strengths include:

- specialization;
- diversity of perspectives;
- explicit Bull/Bear challenge;
- risk review;
- access to heterogeneous data sources.

Warren preserves those ideas.

### Warren extension

Warren adds a shared evidence layer and deterministic calculation layer ahead of agent reasoning.

Key differences:

| Dimension | Tool-driven multi-agent design | Warren design |
|---|---|---|
| Source access | Agents retrieve from tools directly | Evidence Router retrieves before reasoning |
| Evidence representation | Tool results may remain agent-local | Shared normalized evidence objects |
| Duplicate stories | Can appear repeatedly across agents/sources | Explicit event/claim deduplication |
| Source authority | Primarily handled in prompts/reasoning | Explicit source hierarchy and metadata |
| Provenance | Often embedded in agent context | First-class claim/source relationship |
| Structured calculations | May be performed by agents/tools | Deterministic engine for scores, ratios and DCF |
| Missing data | Agent-dependent handling | Explicit source status and confidence reduction |
| Cost | Agents may repeat retrieval | Evidence acquired once and reused |
| Auditability | Reconstruct agent/tool trajectories | Inspect claims, sources, calculations and synthesis |
| Final output | Trade/research recommendation | Attractive / Watch / Avoid + confidence + thesis-break conditions |

---

## 3. Why a centralized Evidence Router may improve end-user value

### 3.1 Broader coverage without repeated searching

Warren can combine:

- SEC/EDGAR and official regulatory sources;
- company investor-relations releases;
- structured market/fundamental providers;
- price and volume history;
- analyst estimates and revisions;
- insider transactions;
- technical indicators;
- financial news;
- web discovery;
- social/sentiment sources;
- macro/government sources.

The user receives broad coverage without requiring every analyst to independently retrieve the same company information.

### 3.2 Deduplication prevents false corroboration

One company event can be syndicated through many outlets.

Example:

```text
Company cuts guidance
  -> company IR release
  -> SEC 8-K
  -> Reuters story
  -> Yahoo syndication
  -> aggregator copy
  -> Reddit discussion
```

Treating those as six independent facts can over-weight one event.

Warren should instead construct something like:

```text
Evidence Claim
Claim: Company reduced FY27 revenue guidance.
Primary source: Company investor-relations release
Independent corroboration: SEC 8-K, Reuters
Syndicated/secondary mentions: Yahoo, aggregator feeds
Social reaction: Reddit
Authority: High
Freshness: 3 hours
```

This gives analysts a cleaner representation of the evidence landscape.

### 3.3 Source authority and source depth are distinct

An authoritative source is only useful to the depth actually retrieved.

Examples:

- Filing metadata proves that a filing exists; it does not prove Warren read the filing body.
- A headline proves the title was published; it does not reveal the unseen article.
- XBRL facts can support numerical calculations directly.
- An official earnings release can support management-guidance claims.

Warren treats **authority** and **retrieval depth** separately to reduce overclaiming.

### 3.4 Facts and interpretations remain separate

Example:

```text
FACTS
Revenue grew 12%.
Forward P/E = 34x.
Management reduced guidance.

INTERPRETATIONS
Bull: durable margins and growth justify the premium.
Bear: the multiple already prices in too much growth.
Risk: lower guidance increases execution and expectation risk.

DECISION
WATCH - Medium confidence
```

This structure lets users inspect the facts even when they disagree with Warren's interpretation.

### 3.5 Contradictory evidence becomes visible

Warren should not collapse disagreement prematurely.

Examples:

- strong reported growth but falling analyst estimates;
- positive company guidance but weakening industry demand;
- improving margins but expensive valuation;
- positive social sentiment but deteriorating fundamentals.

The evidence layer can surface these contradictions before Bull/Bear/Risk agents reason over them.

---

## 4. Why deterministic calculations matter

LLMs are useful for synthesis and argumentation, but Warren should not depend on an LLM for calculations that can be performed deterministically.

Deterministic components should include, where possible:

- valuation ratios;
- growth rates;
- margin trends;
- free-cash-flow yield;
- leverage measures;
- technical indicators;
- category scores;
- DCF calculations and sensitivity tables;
- data-coverage metrics.

The LLM's role is then to explain what those calculations imply, challenge assumptions, and synthesize competing evidence.

Potential benefits:

- repeatability;
- easier testing;
- reduced numerical hallucination;
- lower token usage;
- clearer model-vs-calculation boundaries;
- easier methodology versioning.

---

## 5. Why evidence reuse may reduce cost

A direct multi-agent implementation may allow several agents to perform overlapping retrieval:

```text
Fundamental agent -> search/fetch
News agent        -> search/fetch
Bull agent        -> search/fetch
Bear agent        -> search/fetch
Risk agent        -> search/fetch
```

Warren's target architecture is:

```text
Evidence Router -> retrieve once
                    |
        reusable normalized evidence
          /        |        \
       Bull       Bear      Risk
```

Potential savings come from:

- fewer duplicate API/search calls;
- fewer duplicate documents in prompts;
- caching evidence independently of LLM output;
- using deterministic preprocessing before expensive reasoning;
- routing only ambiguous/high-value questions to stronger models;
- paying for premium evidence only when cheaper evidence is insufficient.

This is a testable cost hypothesis, not yet a proven production result.

---

## 6. Cost-aware source acquisition

Warren should optimize **end-user research value first**, then cost.

A proposed source policy for the U.S.-equities V1:

1. **Primary sources first:** SEC/EDGAR, company investor relations and official government data.
2. **Structured aggregator second:** use a provider for normalized prices, fundamentals, estimates, insiders, news/sentiment or parsed filings where it materially saves engineering effort.
3. **Web discovery third:** search for recent company, industry and regulatory developments not adequately covered by structured feeds.
4. **Social evidence selectively:** use sources such as Reddit for sentiment and emerging narratives, not as substitutes for financial facts.
5. **Premium retrieval on demand:** purchase additional evidence only when it can materially reduce uncertainty in the current analysis.

This supports a future **evidence budget per analysis** rather than an unconstrained number of provider calls.

---

## 7. Proposed source hierarchy

Source hierarchy should affect evidence weighting, but not prevent lower-tier sources from contributing to the questions they answer well.

```text
Tier 1 - Primary / authoritative
SEC filings
Company investor relations
Official government data

Tier 2 - Structured/licensed financial providers
Market data
Fundamentals
Estimates
Insider data
Parsed filings

Tier 3 - High-quality financial journalism
Major financial/news organizations

Tier 4 - Other reputable secondary sources
Industry publications
Specialist financial sites

Tier 5 - Social / community evidence
Reddit
Other social platforms
```

A Tier 5 source may be highly relevant to **sentiment**, while remaining weak evidence for a reported financial fact.

---

## 8. Marketing-safe differentiation today

These claims describe the architecture and can be communicated without claiming superior investment performance:

### Evidence before opinion

Warren collects and structures evidence before asking agents to form an investment view.

### One fact, not five headlines

Warren is designed to deduplicate syndicated stories and distinguish independent corroboration from repeated coverage of the same event.

### Facts are inspectable

The user should be able to trace important claims back to the source and understand when evidence is unavailable or incomplete.

### Numbers are calculated, not improvised

Structured financial calculations and DCF outputs are intended to be deterministic and reproducible rather than generated as prose by an LLM.

### Bull, Bear and Risk see the same evidence

Competing agents reason over the same normalized evidence packet, making disagreement primarily about interpretation rather than inconsistent fact collection.

### Confidence reflects evidence quality

Missing or contradictory evidence should reduce confidence instead of being silently filled from model memory.

### Warren can say what would change its mind

The conclusion includes thesis-break or thesis-improvement conditions so the user can monitor the investment thesis over time.

---

## 9. Claims that require validation before marketing

Do **not** state these as facts until evaluation supports them:

- Warren is more accurate than TradingAgents.
- Warren produces higher investment returns.
- Warren reduces hallucinations by X%.
- Warren is cheaper per analysis by X%.
- Evidence deduplication improves returns.
- Warren's confidence labels are calibrated probabilities.
- Multi-agent Warren outperforms a strong single-agent baseline.

These should become research questions.

---

## 10. Research-paper hypotheses

### H1 - Evidence normalization improves factuality

A centralized evidence layer reduces unsupported factual claims compared with independent agent retrieval.

**Measure:** unsupported-claim rate, citation correctness, evidence-overreach rate.

### H2 - Deduplication reduces evidence overweighting

Event/claim deduplication reduces the tendency to over-weight syndicated news.

**Measure:** recommendation/view changes under duplicated vs deduplicated evidence packets.

### H3 - Shared evidence improves debate quality

Bull/Bear/Risk agents using the same evidence packet produce disagreements that are more interpretive and less factual than agents independently retrieving evidence.

**Measure:** factual contradictions between agents, argument diversity, evidence utilization.

### H4 - Deterministic calculations improve numerical reliability

Moving financial calculations out of LLM reasoning reduces numerical errors without reducing explanation quality.

**Measure:** calculation-error rate, repeatability, token cost.

### H5 - Evidence reuse reduces system cost

Centralized retrieval and caching reduce total provider calls and prompt tokens compared with independent retrieval by every agent.

**Measure:** API calls, retrieved bytes/documents, input tokens, latency and dollars per analysis.

### H6 - Explicit evidence coverage improves confidence calibration

Confidence based partly on source coverage/freshness is better calibrated than confidence generated from reasoning text alone.

**Measure:** factual accuracy/recommendation stability by confidence bucket.

### H7 - Multi-agent challenge adds value beyond a single strong model

Bull/Bear/Risk challenge improves identification of risks, counterarguments and thesis-break conditions compared with a single-agent analysis using the same evidence.

**Measure:** expert ratings, risk recall, counterargument coverage, factuality and cost.

---

## 11. Proposed experimental comparison

Compare at least four architectures using the **same companies and point-in-time evidence**:

### A. Single-agent baseline

One strong reasoning model receives the complete normalized evidence packet.

### B. Tool-driven multi-agent baseline

Specialized agents independently retrieve evidence and then debate/synthesize.

### C. Warren shared-evidence multi-agent

Evidence Router collects/normalizes once; specialized agents reason over the shared packet; Bull/Bear/Risk challenge; final evaluator synthesizes.

### D. Warren without debate

Same Evidence Router and deterministic calculations as C, but only one final evaluator.

This separates the contribution of:

- better evidence architecture;
- deterministic calculations;
- multi-agent debate.

Potential evaluation dimensions:

- factuality;
- citation correctness;
- unsupported claims;
- evidence coverage;
- risk identification;
- thesis quality;
- recommendation stability;
- calibration;
- latency;
- LLM tokens;
- external API cost;
- eventual benchmark-relative investment outcomes.

---

## 12. Potential paper positioning

A possible research framing:

> **From Tool-Using Agents to Evidence-Centric Multi-Agent Research: Separating Fact Acquisition, Deterministic Analysis and Adversarial Interpretation in Financial Decision Support**

Alternative positioning:

> Many multi-agent systems focus on how agents debate. Warren asks an earlier question: **what evidence should the agents be allowed to debate, and how should that evidence be represented before reasoning begins?**

The proposed contribution is therefore not simply "more agents." It is the combination of:

1. heterogeneous source aggregation;
2. evidence normalization and provenance;
3. event/claim deduplication;
4. deterministic financial computation;
5. shared evidence across competing agents;
6. explicit missing-data/confidence handling;
7. cost-aware evidence acquisition;
8. adversarial Bull/Bear/Risk synthesis.

---

## 13. Product narrative to preserve

The long-term Warren proposition can be summarized as:

> **Warren does not ask an AI to guess what a stock is worth. It builds an auditable evidence base, calculates what can be calculated, asks competing research agents to challenge the interpretation, and shows the user both the conclusion and what could make it wrong.**

This statement describes the intended product architecture. It should remain aligned with actual implemented behavior as Warren evolves.
