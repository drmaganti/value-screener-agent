from __future__ import annotations

import asyncio
import json
import os

import httpx

from ..models import CategoryScores, DeepAnalysis, MetricSnapshot


class GeminiDeepAnalysisProvider:
    """TradingAgents-inspired bull/bear/risk debate followed by final synthesis."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def _generate(self, prompt: str) -> dict:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Warren deep mode")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.15, "responseMimeType": "application/json"},
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, params={"key": self.api_key}, json=body)
            response.raise_for_status()
            payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

    @staticmethod
    def _evidence(metrics: MetricSnapshot, scores: CategoryScores) -> str:
        return json.dumps(
            {"metrics": metrics.model_dump(exclude_none=True), "scores": scores.model_dump()},
            separators=(",", ":"),
        )

    async def analyze(self, metrics: MetricSnapshot, scores: CategoryScores) -> tuple[DeepAnalysis, str | None]:
        evidence = self._evidence(metrics, scores)
        shared = (
            "Use ONLY the supplied evidence. Do not invent news, forecasts, competitors, "
            "prices, ratios, catalysts, or facts. Explicitly identify missing evidence. "
            "Distinguish business quality from stock attractiveness."
        )

        bull_prompt = f"""You are Warren's independent BULL analyst. {shared}
Evidence: {evidence}
Return JSON only: {{"arguments":[3-5 concise strings],"weaknesses":[1-3 strings]}}."""
        bear_prompt = f"""You are Warren's independent BEAR analyst. {shared}
Evidence: {evidence}
Return JSON only: {{"arguments":[3-5 concise strings],"weaknesses":[1-3 strings]}}."""
        risk_prompt = f"""You are Warren's independent RISK reviewer. {shared}
Evidence: {evidence}
Return JSON only: {{"risks":[3-5 concise strings],"missing_evidence":[0-5 strings],"summary":"string"}}."""

        bull, bear, risk = await asyncio.gather(
            self._generate(bull_prompt),
            self._generate(bear_prompt),
            self._generate(risk_prompt),
        )

        final_prompt = f"""You are Warren's FINAL investment research evaluator. {shared}
Structured evidence: {evidence}
Bull analyst: {json.dumps(bull)}
Bear analyst: {json.dumps(bear)}
Risk reviewer: {json.dumps(risk)}

Synthesize rather than vote. When evidence is incomplete, reduce confidence. Return JSON only with exactly:
{{"thesis":"string","positives":[3-5 strings],"concerns":[3-5 strings],"bull_case":[2-4 strings],"bear_case":[2-4 strings],"risks":[2-5 strings],"what_would_change_view":[2-4 strings],"verdict":"string","confidence":"low|medium|high"}}."""
        final = await self._generate(final_prompt)
        return DeepAnalysis.model_validate(final), self.model
