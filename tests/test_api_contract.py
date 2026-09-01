from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import AnalyzeRequest


def test_screen_requires_tickers():
    with pytest.raises(ValidationError):
        AnalyzeRequest(mode="screen")


def test_screen_rejects_single_ticker():
    with pytest.raises(ValidationError):
        AnalyzeRequest(mode="screen", ticker="AAPL", tickers=["MSFT"])


def test_deep_requires_ticker():
    with pytest.raises(ValidationError):
        AnalyzeRequest(mode="deep")


def test_deep_rejects_ticker_list():
    with pytest.raises(ValidationError):
        AnalyzeRequest(mode="deep", ticker="AAPL", tickers=["MSFT"])


def test_valid_mode_shapes():
    screen = AnalyzeRequest(mode="screen", tickers=["AAPL", "MSFT"])
    deep = AnalyzeRequest(mode="deep", ticker="AAPL")

    assert screen.mode == "screen"
    assert deep.mode == "deep"


def test_methodology_page_is_served():
    client = TestClient(app)
    response = client.get("/methodology")

    assert response.status_code == 200
    assert "Understand the reasoning, not just the rating." in response.text
    assert "Attractive" in response.text
    assert "Watch" in response.text
    assert "Avoid" in response.text
    assert "DCF" in response.text
