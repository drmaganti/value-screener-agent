from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

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

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "warren"}


@app.get("/methodology", include_in_schema=False)
def methodology_page() -> FileResponse:
    return FileResponse(WEB_DIR / "methodology.html", media_type="text/html")


@app.get("/roadmap", include_in_schema=False)
def roadmap_page() -> FileResponse:
    return FileResponse(WEB_DIR / "roadmap.html", media_type="text/html")


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
