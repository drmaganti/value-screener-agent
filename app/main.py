from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .llm import build_deep_analysis
from .models import AnalyzeRequest, AnalyzeResponse
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


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        metrics = fetch_metrics(request.ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to fetch market data for {request.ticker.upper()}") from exc

    scores = score_metrics(metrics)
    missing_data = [
        field
        for field, value in metrics.model_dump().items()
        if field not in {"ticker", "company_name", "sector", "industry", "currency"} and value is None
    ]

    analysis = None
    model = None
    if request.mode == "deep":
        try:
            analysis, model = await build_deep_analysis(metrics, scores, request.depth)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Deep analysis failed") from exc

    return AnalyzeResponse(
        ticker=metrics.ticker,
        mode=request.mode,
        depth=request.depth,
        metrics=metrics,
        scores=scores,
        missing_data=missing_data,
        analysis=analysis,
        model=model,
    )
