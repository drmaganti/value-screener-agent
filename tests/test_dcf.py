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
            total_revenue=100_000_000_000,
            total_cash=20_000_000_000,
            total_debt=5_000_000_000,
            shares_outstanding=1_000_000_000,
            market_cap=100_000_000_000,
            beta=1.2,
            historical_free_cash_flow=[8_000_000_000, 10_000_000_000, 12_000_000_000],
            revenue_growth=0.08,
            earnings_growth=0.10,
        )
    )

    assert result.status == "available"
    assert result.methodology_version == "dcf-v1.0"
    assert [scenario.name for scenario in result.scenarios] == ["bear", "base", "bull"]
    values = [scenario.fair_value_per_share for scenario in result.scenarios]
    assert values == sorted(values)
    assert len(result.sensitivity) == 9
    assert result.net_cash == 15_000_000_000
    assert result.base_free_cash_flow == 10_000_000_000
    assert result.normalization_method.startswith("Median")
    assert result.scenarios[1].fcf_growth == pytest.approx(0.09)
    assert "forward revenue/earnings" in result.scenarios[1].assumption_basis
    assert result.scenarios[1].revenue_growth == pytest.approx(0.09)
    assert result.scenarios[0].ending_fcf_margin < result.scenarios[0].starting_fcf_margin
    assert result.scenarios[2].ending_fcf_margin > result.scenarios[2].starting_fcf_margin
    assert result.discount_rate_details.beta == 1.2
    assert result.discount_rate_details.debt_weight == pytest.approx(5 / 105)
    assert result.scenarios[1].discount_rate == pytest.approx(
        result.discount_rate_details.applied_discount_rate
    )


def test_dcf_labels_beta_and_capital_structure_fallbacks():
    result = calculate_dcf(
        MetricSnapshot(
            ticker="TEST",
            price=100,
            free_cash_flow=10_000_000_000,
            total_revenue=100_000_000_000,
            total_cash=20_000_000_000,
            total_debt=5_000_000_000,
            shares_outstanding=1_000_000_000,
        )
    )

    details = result.discount_rate_details
    assert details.beta == 1.0
    assert details.equity_weight == 1.0
    assert any("Beta was missing" in item for item in details.assumption_basis)
    assert any("all-equity" in item for item in details.assumption_basis)


def test_dcf_uses_documented_fallbacks_when_history_and_estimates_are_sparse():
    result = calculate_dcf(
        MetricSnapshot(
            ticker="TEST",
            price=100,
            free_cash_flow=10_000_000_000,
            total_revenue=100_000_000_000,
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
        "total_revenue": 100_000_000_000,
        "total_cash": 20_000_000_000,
        "total_debt": 5_000_000_000,
        "shares_outstanding": 1_000_000_000,
        **updates,
    }

    result = calculate_dcf(MetricSnapshot(**values))

    assert result.status == "unavailable"
    assert reason in result.reason
    assert result.scenarios == []
