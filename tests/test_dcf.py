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
        )
    )

    assert result.status == "available"
    assert result.methodology_version == "dcf-v0.1"
    assert [scenario.name for scenario in result.scenarios] == ["bear", "base", "bull"]
    values = [scenario.fair_value_per_share for scenario in result.scenarios]
    assert values == sorted(values)
    assert len(result.sensitivity) == 9
    assert result.net_cash == 15_000_000_000


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
