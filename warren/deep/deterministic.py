from __future__ import annotations

from ..models import CategoryScores, DeepAnalysis, EvidenceBundle, MetricSnapshot


class DeterministicDeepAnalysisProvider:
    """Evidence-aware fallback used when an LLM provider is not configured.

    The fallback deliberately does not invent facts. It converts Warren's
    deterministic category scores and retrieved evidence into a concise,
    explainable research summary so Deep mode remains usable without an API key.
    Technical and insider observations can enrich the narrative but do not alter
    the current uncalibrated verdict thresholds.
    """

    @staticmethod
    def _pct(value: float | None) -> str | None:
        if value is None:
            return None
        return f"{value * 100:.1f}%"

    @staticmethod
    def _category_label(score: float) -> str:
        if score >= 80:
            return "strong"
        if score >= 65:
            return "above average"
        if score >= 50:
            return "mixed"
        if score >= 35:
            return "weak"
        return "very weak"

    @staticmethod
    def _verdict(scores: CategoryScores) -> str:
        if (
            scores.overall >= 72
            and scores.valuation >= 58
            and scores.fundamentals >= 62
            and scores.business_quality >= 60
            and scores.risk_resilience >= 50
        ):
            return "attractive"
        if (
            scores.overall < 45
            or scores.fundamentals < 35
            or scores.business_quality < 35
            or scores.risk_resilience < 30
        ):
            return "avoid"
        return "watch"

    @staticmethod
    def _confidence(metrics: MetricSnapshot, evidence: EvidenceBundle) -> str:
        fields = [
            metrics.trailing_pe,
            metrics.forward_pe,
            metrics.free_cash_flow,
            metrics.revenue_growth,
            metrics.earnings_growth,
            metrics.operating_margin,
            metrics.return_on_equity,
            metrics.debt_to_equity,
            metrics.current_ratio,
        ]
        missing = sum(v is None for v in fields)
        problematic_sources = sum(
            status.status in {"unavailable", "error"} for status in evidence.source_status
        )
        if missing <= 2 and problematic_sources == 0:
            return "high"
        if missing <= 5 and problematic_sources <= 2:
            return "medium"
        return "low"

    @staticmethod
    def _top_categories(scores: CategoryScores) -> list[tuple[str, float]]:
        values = [
            ("fundamentals", scores.fundamentals),
            ("valuation", scores.valuation),
            ("business quality", scores.business_quality),
            ("growth", scores.growth),
            ("risk resilience", scores.risk_resilience),
            ("market context", scores.market_context),
        ]
        return sorted(values, key=lambda item: item[1], reverse=True)

    @staticmethod
    def _technical_context(evidence: EvidenceBundle) -> tuple[list[str], list[str]]:
        if not evidence.technical:
            return [], []
        technical = evidence.technical[0]
        supportive: list[str] = []
        cautious: list[str] = []

        if technical.close is not None and technical.sma_200 is not None:
            if technical.close >= technical.sma_200:
                supportive.append(
                    f"Price is above the 200-day moving average ({technical.close:.2f} vs {technical.sma_200:.2f}), a supportive long-term trend observation."
                )
            else:
                cautious.append(
                    f"Price is below the 200-day moving average ({technical.close:.2f} vs {technical.sma_200:.2f}), a weak long-term trend observation."
                )
        if technical.close is not None and technical.sma_50 is not None:
            if technical.close >= technical.sma_50:
                supportive.append(
                    f"Price is above the 50-day moving average ({technical.close:.2f} vs {technical.sma_50:.2f})."
                )
            else:
                cautious.append(
                    f"Price is below the 50-day moving average ({technical.close:.2f} vs {technical.sma_50:.2f})."
                )
        if technical.rsi_14 is not None:
            if technical.rsi_14 >= 70:
                cautious.append(f"14-day RSI is {technical.rsi_14:.1f}, an elevated short-term momentum reading.")
            elif technical.rsi_14 <= 30:
                cautious.append(f"14-day RSI is {technical.rsi_14:.1f}, reflecting weak/oversold short-term momentum.")
        if technical.macd is not None and technical.macd_signal is not None:
            if technical.macd >= technical.macd_signal:
                supportive.append(
                    f"MACD is above its signal line ({technical.macd:.3f} vs {technical.macd_signal:.3f})."
                )
            else:
                cautious.append(
                    f"MACD is below its signal line ({technical.macd:.3f} vs {technical.macd_signal:.3f})."
                )
        return supportive, cautious

    @staticmethod
    def _insider_context(evidence: EvidenceBundle) -> tuple[list[str], list[str]]:
        supportive: list[str] = []
        cautious: list[str] = []
        for item in evidence.insider_transactions[:5]:
            transaction = (item.transaction or "").lower()
            actor = item.insider or "an insider"
            date_text = item.start_date.isoformat() if item.start_date else "an unspecified date"
            if "purchase" in transaction or "buy" in transaction:
                supportive.append(
                    f"Structured insider data reports a purchase by {actor} on {date_text}; insider activity is contextual evidence, not a standalone thesis."
                )
            elif "sale" in transaction or "sell" in transaction:
                cautious.append(
                    f"Structured insider data reports a sale by {actor} on {date_text}; insider sales may be scheduled or liquidity-driven and are not independently decisive."
                )
        return supportive, cautious

    async def analyze(
        self,
        metrics: MetricSnapshot,
        scores: CategoryScores,
        evidence: EvidenceBundle,
    ) -> tuple[DeepAnalysis, str | None]:
        ranked = self._top_categories(scores)
        verdict = self._verdict(scores)
        confidence = self._confidence(metrics, evidence)

        positives: list[str] = []
        concerns: list[str] = []

        for label, score in ranked[:3]:
            if score >= 60:
                positives.append(f"{label.title()} scores {score:.0f}/100, a {self._category_label(score)} reading in Warren's current framework.")

        if metrics.free_cash_flow is not None:
            positives.append(
                "Free cash flow is positive."
                if metrics.free_cash_flow > 0
                else "Free cash flow is negative, which weakens the investment case."
            )
        if metrics.operating_margin is not None and metrics.operating_margin >= 0.15:
            positives.append(f"Operating margin is {self._pct(metrics.operating_margin)}, supporting business-quality resilience.")
        if metrics.revenue_growth is not None and metrics.revenue_growth >= 0.08:
            positives.append(f"Reported revenue growth is {self._pct(metrics.revenue_growth)}.")

        for label, score in reversed(ranked[-3:]):
            if score < 55:
                concerns.append(f"{label.title()} scores {score:.0f}/100 and is one of the weaker parts of the current setup.")

        if metrics.trailing_pe is not None and metrics.trailing_pe >= 35:
            concerns.append(f"Trailing P/E is {metrics.trailing_pe:.1f}x, so the current price embeds a relatively demanding earnings multiple.")
        if metrics.debt_to_equity is not None and metrics.debt_to_equity >= 150:
            concerns.append(f"Debt-to-equity is {metrics.debt_to_equity:.0f}, which warrants closer balance-sheet review.")
        if metrics.current_ratio is not None and metrics.current_ratio < 1:
            concerns.append(f"Current ratio is {metrics.current_ratio:.2f}, indicating limited short-term balance-sheet cushion by this measure.")
        if metrics.earnings_growth is not None and metrics.earnings_growth < 0:
            concerns.append(f"Reported earnings growth is {self._pct(metrics.earnings_growth)}, a negative growth signal.")

        positives = positives[:5] or ["No strong positive signal is available from the currently observed metrics."]
        concerns = concerns[:5] or ["No major quantitative weakness is dominant, but the evidence set remains incomplete and should be reviewed alongside primary sources."]

        technical_support, technical_caution = self._technical_context(evidence)
        insider_support, insider_caution = self._insider_context(evidence)

        bull_case = positives[:3]
        bull_case.extend(technical_support[:1])
        if len(bull_case) < 4:
            bull_case.extend(insider_support[: 4 - len(bull_case)])
        if len(bull_case) < 4 and evidence.estimate_revisions:
            bull_case.append("Analyst estimate/revision evidence is available for review in the evidence packet.")

        bear_case = concerns[:3]
        bear_case.extend(technical_caution[:1])
        if len(bear_case) < 4:
            bear_case.extend(insider_caution[: 4 - len(bear_case)])
        if len(bear_case) < 4 and evidence.source_status:
            unavailable = [s.source for s in evidence.source_status if s.status in {"unavailable", "error"}]
            if unavailable:
                bear_case.append(f"Some evidence sources are unavailable or errored: {', '.join(unavailable[:3])}.")

        risks = concerns[:3]
        risks.extend(insider_caution[:1])
        if not evidence.filings:
            risks.append("No filing evidence is available in the current packet; primary-source review remains important.")
        if not evidence.news and len(risks) < 5:
            risks.append("No recent headline evidence is available in the current packet.")
        risks = risks[:5]

        if verdict == "attractive":
            thesis = (
                f"{metrics.company_name or metrics.ticker} currently screens as Attractive: the overall score is "
                f"{scores.overall:.0f}/100, with sufficiently supportive business quality, fundamentals, valuation and risk resilience. "
                "The conclusion is research-oriented and should be revisited when price, earnings, filings or estimate revisions change."
            )
            changes = [
                "A material deterioration in free cash flow, margins or balance-sheet resilience.",
                "Valuation becoming materially more demanding without a corresponding improvement in growth or fundamentals.",
                "New primary-source evidence that weakens the business-quality or risk thesis.",
            ]
        elif verdict == "avoid":
            thesis = (
                f"{metrics.company_name or metrics.ticker} currently screens as Avoid: the overall score is "
                f"{scores.overall:.0f}/100 and one or more fundamental, quality or risk-resilience dimensions are too weak for a favorable setup."
            )
            changes = [
                "Clear improvement in the weakest fundamental or business-quality factors.",
                "A materially better valuation with evidence that the underlying business is stabilizing.",
                "New filings, earnings or estimate evidence that resolves the dominant downside risks.",
            ]
        else:
            thesis = (
                f"{metrics.company_name or metrics.ticker} currently belongs on Watch: the overall score is "
                f"{scores.overall:.0f}/100, but the evidence does not yet support an Attractive conclusion or an Avoid conclusion. "
                "The setup has meaningful strengths and unresolved trade-offs."
            )
            changes = [
                "A more attractive valuation or stronger free-cash-flow yield without deterioration in quality.",
                "Improving earnings/revenue trends or estimate revisions that strengthen the growth case.",
                "Material deterioration in fundamentals, risk resilience or primary-source evidence, which could move the view to Avoid.",
            ]

        return (
            DeepAnalysis(
                thesis=thesis,
                positives=positives,
                concerns=concerns,
                bull_case=bull_case[:4],
                bear_case=bear_case[:4],
                risks=risks,
                what_would_change_view=changes,
                verdict=verdict,
                confidence=confidence,
            ),
            "deterministic-v1.1",
        )
