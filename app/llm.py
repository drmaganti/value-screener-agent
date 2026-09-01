from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx

from .models import CategoryScores, DeepAnalysis, MetricSnapshot


def _model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required for deep analysis")
    return key


def _evidence(metrics: MetricSnapshot, scores: CategoryScores) -> str:
    payload = {
        "metrics": metrics.model_dump(exclude_none=True),
        "scores": scores.model_dump(),
    }
    return json.dumps(payload, separators=(",", ":"), default=str)


async def _generate(prompt: str) -> str:
    model = _model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, params={"key": _api_key()}, json=body)
        response.raise_for_status()
        data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _final_prompt(metrics: MetricSnapshot, scores: CategoryScores, debate: dict[str, Any]) -> str:
    return f"""You are the final stock research evaluator. Use ONLY the supplied evidence. Do not invent prices, ratios, forecasts, news, competitors, or catalysts. Distinguish business quality from stock valuation. A high-quality company can still be an unattractive stock at the current valuation.

Evidence: {_evidence(metrics, scores)}
Independent bull/bear/risk review: {json.dumps(debate, separators=(",", ":"))}

Return exactly one JSON object with these keys:
thesis (string), positives (array of 3-5 strings), concerns (array of 3-5 strings), bull_case (array of 2-4 strings), bear_case (array of 2-4 strings), risks (array of 2-4 strings), what_would_change_view (array of 2-4 strings), verdict (string), confidence (one of low, medium, high).
If important evidence is missing, say so and reduce confidence. This is research, not financial advice."""


async def build_deep_analysis(metrics: MetricSnapshot, scores: CategoryScores) -> tuple[DeepAnalysis, str]:
    evidence = _evidence(metrics, scores)
    prompts = {
        "bull": f"Act as a skeptical bullish equity researcher. Using ONLY this evidence, return JSON with key arguments (array) and weaknesses (array). Evidence: {evidence}",
        "bear": f"Act as a skeptical bearish equity researcher. Using ONLY this evidence, return JSON with key arguments (array) and weaknesses (array). Evidence: {evidence}",
        "risk": f"Act as an investment risk reviewer. Using ONLY this evidence, return JSON with key risks (array), missing_evidence (array), and risk_summary (string). Evidence: {evidence}",
    }
    bull, bear, risk = await asyncio.gather(*[_generate(prompt) for prompt in prompts.values()])
    debate: dict[str, Any] = {
        "bull": json.loads(bull),
        "bear": json.loads(bear),
        "risk": json.loads(risk),
    }

    raw = await _generate(_final_prompt(metrics, scores, debate))
    return DeepAnalysis.model_validate(json.loads(raw)), _model()
