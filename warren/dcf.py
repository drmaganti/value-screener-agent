from __future__ import annotations

from statistics import median

from .models import DcfResult, DcfScenario, DcfSensitivityPoint, MetricSnapshot


DCF_VERSION = "dcf-v0.2"
FORECAST_YEARS = 5


def _normalized_fcf(metrics: MetricSnapshot) -> tuple[float, str]:
    positive_history = [value for value in metrics.historical_free_cash_flow if value > 0]
    if len(positive_history) >= 2:
        return median(positive_history[-3:]), "Median of up to three positive annual free-cash-flow observations"
    return metrics.free_cash_flow, "Current free cash flow; insufficient positive annual history for normalization"


def _growth_assumptions(metrics: MetricSnapshot) -> tuple[tuple[float, float, float], str]:
    estimates = [
        value
        for value in (metrics.revenue_growth, metrics.earnings_growth)
        if value is not None and -0.20 <= value <= 0.30
    ]
    if estimates:
        base = min(0.12, max(0.02, median(estimates)))
        basis = "Anchored to available Yahoo forward revenue/earnings growth estimates and bounded by methodology limits"
    else:
        base = 0.06
        basis = "Configured fallback; forward revenue/earnings growth estimates unavailable"
    return (max(-0.02, base - 0.04), base, min(0.15, base + 0.03)), basis


def _value(
    base_fcf: float,
    shares: float,
    net_cash: float,
    growth: float,
    discount_rate: float,
    terminal_growth: float,
) -> float:
    projected_fcf = base_fcf
    present_value = 0.0
    for year in range(1, FORECAST_YEARS + 1):
        projected_fcf *= 1 + growth
        present_value += projected_fcf / ((1 + discount_rate) ** year)
    terminal_value = projected_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    equity_value = present_value + terminal_value / ((1 + discount_rate) ** FORECAST_YEARS) + net_cash
    return equity_value / shares


def calculate_dcf(metrics: MetricSnapshot) -> DcfResult:
    required = {
        "free_cash_flow": metrics.free_cash_flow,
        "shares_outstanding": metrics.shares_outstanding,
        "total_cash": metrics.total_cash,
        "total_debt": metrics.total_debt,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        return DcfResult(
            status="unavailable",
            methodology_version=DCF_VERSION,
            reason=f"Missing required inputs: {', '.join(missing)}",
            input_source="Yahoo Finance company snapshot",
            input_as_of=metrics.fetched_at,
        )
    if metrics.free_cash_flow <= 0:
        return DcfResult(
            status="unavailable",
            methodology_version=DCF_VERSION,
            reason="Standard DCF is not run when current free cash flow is non-positive.",
            input_source="Yahoo Finance company snapshot",
            input_as_of=metrics.fetched_at,
        )
    if metrics.shares_outstanding <= 0:
        return DcfResult(
            status="unavailable",
            methodology_version=DCF_VERSION,
            reason="Diluted shares outstanding must be positive.",
            input_source="Yahoo Finance company snapshot",
            input_as_of=metrics.fetched_at,
        )

    base_fcf, normalization_method = _normalized_fcf(metrics)
    growth_rates, growth_basis = _growth_assumptions(metrics)
    net_cash = metrics.total_cash - metrics.total_debt
    scenarios = []
    scenario_inputs = zip(
        ("bear", "base", "bull"),
        growth_rates,
        (0.11, 0.10, 0.09),
        (0.02, 0.025, 0.03),
    )
    for name, growth, discount_rate, terminal_growth in scenario_inputs:
        fair_value = _value(
            base_fcf,
            metrics.shares_outstanding,
            net_cash,
            growth,
            discount_rate,
            terminal_growth,
        )
        upside = None if not metrics.price or metrics.price <= 0 else fair_value / metrics.price - 1
        scenarios.append(
            DcfScenario(
                name=name,
                forecast_years=FORECAST_YEARS,
                fcf_growth=growth,
                discount_rate=discount_rate,
                terminal_growth=terminal_growth,
                fair_value_per_share=round(fair_value, 2),
                upside_downside=upside,
                assumption_basis=growth_basis,
            )
        )

    sensitivity = []
    for discount_rate in (0.09, 0.10, 0.11):
        for terminal_growth in (0.02, 0.025, 0.03):
            sensitivity.append(
                DcfSensitivityPoint(
                    discount_rate=discount_rate,
                    terminal_growth=terminal_growth,
                    fair_value_per_share=round(
                        _value(
                            base_fcf,
                            metrics.shares_outstanding,
                            net_cash,
                            growth_rates[1],
                            discount_rate,
                            terminal_growth,
                        ),
                        2,
                    ),
                )
            )

    return DcfResult(
        status="available",
        methodology_version=DCF_VERSION,
        base_free_cash_flow=base_fcf,
        normalization_method=normalization_method,
        net_cash=net_cash,
        shares_outstanding=metrics.shares_outstanding,
        current_price=metrics.price,
        input_source="Yahoo Finance company snapshot",
        input_as_of=metrics.fetched_at,
        scenarios=scenarios,
        sensitivity=sensitivity,
        caveats=[
            normalization_method + ".",
            growth_basis + ".",
            "DCF is one valuation lens and is highly sensitive to discount and terminal-growth assumptions.",
        ],
    )
