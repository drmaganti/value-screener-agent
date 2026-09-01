from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException

from .llm import build_deep_analysis
from .models import AnalyzeRequest, AnalyzeResponse, ScreenResult
from .provider import fetch_metrics
from .scoring import score_metrics

app = FastAPI(
    title="Stock Analyze API",
    version="0.1.0",
    description="Reusable stock screening and deep-analysis service for Parse and Value Screener.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _missing_fields(metrics) -> list[str]:
    return [
        field
        for field, value in metrics.model_dump().items()
        if field not in {"ticker", "company_name", "sector", "industry", "currency"} and value is None
    ]


async def _screen_one(ticker: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            metrics = await asyncio.to_thread(fetch_metrics, ticker)
            scores = score_metrics(metrics)
            return ScreenResult(
                ticker=metrics.ticker,
                company_name=metrics.company_name,
                sector=metrics.sector,
                price=metrics.price,
                scores=scores,
                missing_data_count=len(_missing_fields(metrics)),
            )
        except Exception:
            return ticker.strip().upper()


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    if request.mode == "screen":
        symbols = list(dict.fromkeys(t.strip().upper() for t in request.tickers or [] if t.strip()))
        semaphore = asyncio.Semaphore(8)
        raw = await asyncio.gather(*[_screen_one(symbol, semaphore) for symbol in symbols])

        results = [item for item in raw if isinstance(item, ScreenResult)]
        failed = [item for item in raw if isinstance(item, str)]
        results = [item for item in results if item.scores.overall >= request.min_score]
        results.sort(key=lambda item: item.scores.overall, reverse=True)
        results = results[: request.top_n]

        return AnalyzeResponse(
            mode="screen",
            screened_count=len(symbols),
            failed_tickers=failed,
            results=results,
        )

    try:
        metrics = await asyncio.to_thread(fetch_metrics, request.ticker or "")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to fetch market data for {(request.ticker or '').upper()}") from exc

    scores = score_metrics(metrics)
    missing_data = _missing_fields(metrics)

    try:
        analysis, model = await build_deep_analysis(metrics, scores)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Deep analysis failed") from exc

    return AnalyzeResponse(
        mode="deep",
        ticker=metrics.ticker,
        metrics=metrics,
        scores=scores,
        missing_data=missing_data,
        analysis=analysis,
        model=model,
    )
