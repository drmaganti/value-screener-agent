from __future__ import annotations

import pytest
from pydantic import ValidationError

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
