from __future__ import annotations

import pytest

from warren.dcf import calculate_dcf
from warren.models import MetricSnapshot


def test_dcf_produces_ordered_scenarios_and_sensitivity():
    result = calculate_dcf(
        MetricSnapshot(
            ticker="TEST",
            price=100,
            free_cash_flow=10_000_000_000,
            total_cash=20_000_000_000,
            total_debt=5_000_000_000,
            shares_outstanding=1_000_000_000,
            historical_free_cash_flow=[8_000_000_000, 10_000_000_000, 12_000_000_000],
            revenue_growth=0.08,
            earnings_growth=0.10,
        )
    )

    assert result.status == "available"
    assert result.methodology_version == "dcf-v0.2"
    assert [scenario.name for scenario in result.scenarios] == ["bear", "base", "bull"]
    values = [scenario.fair_value_per_share for scenario in result.scenarios]
    assert values == sorted(values)
    assert len(result.sensitivity) == 9
    assert result.net_cash == 15_000_000_000
    assert result.base_free_cash_flow == 10_000_000_000
    assert result.normalization_method.startswith("Median")
    assert result.scenarios[1].fcf_growth == pytest.approx(0.09)
    assert "forward revenue/earnings" in result.scenarios[1].assumption_basis


def test_dcf_uses_documented_fallbacks_when_history_and_estimates_are_sparse():
    result = calculate_dcf(
        MetricSnapshot(
            ticker="TEST",
            price=100,
            free_cash_flow=10_000_000_000,
            total_cash=20_000_000_000,
            total_debt=5_000_000_000,
            shares_outstanding=1_000_000_000,
            historical_free_cash_flow=[9_000_000_000],
        )
    )

    assert result.status == "available"
    assert result.base_free_cash_flow == 10_000_000_000
    assert result.normalization_method.startswith("Current free cash flow")
    assert result.scenarios[1].fcf_growth == pytest.approx(0.06)
    assert "Configured fallback" in result.scenarios[1].assumption_basis


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"free_cash_flow": None}, "free_cash_flow"),
        ({"shares_outstanding": None}, "shares_outstanding"),
        ({"total_cash": None}, "total_cash"),
        ({"total_debt": None}, "total_debt"),
        ({"free_cash_flow": -1}, "non-positive"),
    ],
)
def test_dcf_fails_transparently_when_inputs_are_unsuitable(updates, reason):
    values = {
        "ticker": "TEST",
        "price": 100,
        "free_cash_flow": 10_000_000_000,
        "total_cash": 20_000_000_000,
        "total_debt": 5_000_000_000,
        "shares_outstanding": 1_000_000_000,
        **updates,
    }

    result = calculate_dcf(MetricSnapshot(**values))

    assert result.status == "unavailable"
    assert reason in result.reason
    assert result.scenarios == []
