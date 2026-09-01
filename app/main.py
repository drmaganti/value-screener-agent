from __future__ import annotations

from fastapi import FastAPI, HTTPException

from warren.deep import GeminiDeepAnalysisProvider
from warren.engine import Warren
from warren.evidence import CompositeEvidenceProvider, FredMacroEvidenceProvider, SecFilingEvidenceProvider, YahooEvidenceProvider
from warren.providers import YFinanceMarketDataProvider

from .models import AnalyzeRequest, AnalyzeResponse

engine = Warren(
    market_data=YFinanceMarketDataProvider(),
    deep_analysis=GeminiDeepAnalysisProvider(),
    evidence=CompositeEvidenceProvider(
        [
            SecFilingEvidenceProvider(),
            YahooEvidenceProvider(),
            FredMacroEvidenceProvider(),
        ]
    ),
)

app = FastAPI(
    title="Warren Stock Intelligence API",
    version="0.3.0",
    description="Reusable stock screening and source-grounded TradingAgents-inspired deep analysis for any client application.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "warren"}


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    if request.mode == "screen":
        try:
            result = await engine.screen(
                request.tickers or [],
                top_n=request.top_n,
                min_score=request.min_score,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Screening failed") from exc
        return AnalyzeResponse.model_validate({"mode": "screen", **result.model_dump()})

    try:
        result = await engine.deep(request.ticker or "")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Deep analysis failed") from exc

    return AnalyzeResponse.model_validate({"mode": "deep", **result.model_dump()})
