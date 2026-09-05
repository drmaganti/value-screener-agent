from __future__ import annotations

from statistics import median

from .models import DcfResult, DcfScenario, DcfSensitivityPoint, DiscountRateDetails, MetricSnapshot

DCF_VERSION = "dcf-v1.0"
FORECAST_YEARS = 5
RISK_FREE_RATE = 0.0425
EQUITY_RISK_PREMIUM = 0.055
PRE_TAX_COST_OF_DEBT = 0.055
TAX_RATE = 0.21
MIN_WACC = 0.07
MAX_WACC = 0.15


def _normalized_fcf(metrics: MetricSnapshot) -> tuple[float, str]:
    positive_history = [value for value in metrics.historical_free_cash_flow if value > 0]
    if len(positive_history) >= 2:
        return median(positive_history[-3:]), "Median of up to three positive annual free-cash-flow observations"
    return metrics.free_cash_flow, "Current free cash flow; insufficient positive annual history for normalization"


def _growth_assumptions(metrics: MetricSnapshot) -> tuple[tuple[float, float, float], str]:
    estimates = [value for value in (metrics.revenue_growth, metrics.earnings_growth) if value is not None and -0.20 <= value <= 0.30]
    if estimates:
        base = min(0.12, max(0.02, median(estimates)))
        basis = "Anchored to available Yahoo forward revenue/earnings growth estimates and bounded by methodology limits"
    else:
        base = 0.06
        basis = "Configured fallback; forward revenue/earnings growth estimates unavailable"
    return (max(-0.02, base - 0.04), base, min(0.15, base + 0.03)), basis


def _discount_rate(metrics: MetricSnapshot) -> DiscountRateDetails:
    basis = ["Risk-free rate, equity risk premium, pre-tax debt cost and tax rate are configured methodology assumptions."]
    beta = metrics.beta if metrics.beta is not None and 0.25 <= metrics.beta <= 3 else 1.0
    basis.append("Beta came from the Yahoo Finance company snapshot." if beta == metrics.beta else "Beta was missing or outside the supported range; 1.0 was used.")
    equity_value = metrics.market_cap if metrics.market_cap is not None and metrics.market_cap > 0 else None
    debt_value = metrics.total_debt if metrics.total_debt is not None and metrics.total_debt >= 0 else None
    if equity_value is None or debt_value is None or equity_value + debt_value <= 0:
        equity_weight, debt_weight = 1.0, 0.0
        basis.append("Capital-structure inputs were incomplete; an all-equity weighting was used.")
    else:
        total_capital = equity_value + debt_value
        equity_weight, debt_weight = equity_value / total_capital, debt_value / total_capital
        basis.append("Equity and debt weights came from current market capitalization and reported total debt.")
    cost_of_equity = RISK_FREE_RATE + beta * EQUITY_RISK_PREMIUM
    calculated_wacc = equity_weight * cost_of_equity + debt_weight * PRE_TAX_COST_OF_DEBT * (1 - TAX_RATE)
    applied = min(MAX_WACC, max(MIN_WACC, calculated_wacc))
    if applied != calculated_wacc:
        basis.append(f"Calculated WACC was bounded to the {MIN_WACC:.0%}–{MAX_WACC:.0%} methodology range.")
    return DiscountRateDetails(method="CAPM cost of equity plus after-tax debt cost", risk_free_rate=RISK_FREE_RATE, equity_risk_premium=EQUITY_RISK_PREMIUM, beta=beta, cost_of_equity=cost_of_equity, pre_tax_cost_of_debt=PRE_TAX_COST_OF_DEBT, tax_rate=TAX_RATE, equity_weight=equity_weight, debt_weight=debt_weight, calculated_wacc=calculated_wacc, applied_discount_rate=applied, assumption_basis=basis)


def _value(base_fcf: float, base_revenue: float, shares: float, net_cash: float, revenue_growth: float, margin_change: float, discount_rate: float, terminal_growth: float) -> tuple[float, float]:
    projected_revenue = base_revenue
    starting_margin = base_fcf / base_revenue
    projected_fcf = base_fcf
    present_value = 0.0
    for year in range(1, FORECAST_YEARS + 1):
        projected_revenue *= 1 + revenue_growth
        projected_margin = starting_margin + margin_change * year / FORECAST_YEARS
        projected_fcf = projected_revenue * projected_margin
        present_value += projected_fcf / ((1 + discount_rate) ** year)
    terminal_value = projected_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    equity_value = present_value + terminal_value / ((1 + discount_rate) ** FORECAST_YEARS) + net_cash
    return equity_value / shares, projected_fcf


def calculate_dcf(metrics: MetricSnapshot) -> DcfResult:
    required = {"free_cash_flow": metrics.free_cash_flow, "total_revenue": metrics.total_revenue, "shares_outstanding": metrics.shares_outstanding, "total_cash": metrics.total_cash, "total_debt": metrics.total_debt}
    missing = [name for name, value in required.items() if value is None]
    common = {"methodology_version": DCF_VERSION, "input_source": "Yahoo Finance company snapshot", "input_as_of": metrics.fetched_at}
    if missing:
        return DcfResult(status="unavailable", reason=f"Missing required inputs: {', '.join(missing)}", **common)
    if metrics.free_cash_flow <= 0 or metrics.total_revenue <= 0:
        return DcfResult(status="unavailable", reason="Standard DCF is not run with non-positive current free cash flow or revenue.", **common)
    if metrics.shares_outstanding <= 0:
        return DcfResult(status="unavailable", reason="Diluted shares outstanding must be positive.", **common)

    base_fcf, normalization_method = _normalized_fcf(metrics)
    growth_rates, growth_basis = _growth_assumptions(metrics)
    discount_details = _discount_rate(metrics)
    base_discount_rate = discount_details.applied_discount_rate
    net_cash = metrics.total_cash - metrics.total_debt
    starting_margin = base_fcf / metrics.total_revenue
    scenarios = []
    inputs = zip(("bear", "base", "bull"), growth_rates, (-0.01, 0.0, 0.01), (min(MAX_WACC, base_discount_rate + 0.01), base_discount_rate, max(MIN_WACC, base_discount_rate - 0.01)), (0.02, 0.025, 0.03))
    for name, revenue_growth, margin_change, discount_rate, terminal_growth in inputs:
        fair_value, final_fcf = _value(base_fcf, metrics.total_revenue, metrics.shares_outstanding, net_cash, revenue_growth, margin_change, discount_rate, terminal_growth)
        scenarios.append(DcfScenario(name=name, forecast_years=FORECAST_YEARS, fcf_growth=(final_fcf / base_fcf) ** (1 / FORECAST_YEARS) - 1, revenue_growth=revenue_growth, starting_fcf_margin=starting_margin, ending_fcf_margin=starting_margin + margin_change, discount_rate=discount_rate, terminal_growth=terminal_growth, fair_value_per_share=round(fair_value, 2), upside_downside=None if not metrics.price or metrics.price <= 0 else fair_value / metrics.price - 1, assumption_basis=growth_basis))

    sensitivity = []
    for discount_rate in (max(MIN_WACC, base_discount_rate - 0.01), base_discount_rate, min(MAX_WACC, base_discount_rate + 0.01)):
        for terminal_growth in (0.02, 0.025, 0.03):
            fair_value, _ = _value(base_fcf, metrics.total_revenue, metrics.shares_outstanding, net_cash, growth_rates[1], 0.0, discount_rate, terminal_growth)
            sensitivity.append(DcfSensitivityPoint(discount_rate=discount_rate, terminal_growth=terminal_growth, fair_value_per_share=round(fair_value, 2)))

    return DcfResult(status="available", base_free_cash_flow=base_fcf, normalization_method=normalization_method, discount_rate_details=discount_details, net_cash=net_cash, shares_outstanding=metrics.shares_outstanding, current_price=metrics.price, scenarios=scenarios, sensitivity=sensitivity, caveats=[normalization_method + ".", growth_basis + ".", "Revenue growth and FCF-margin paths are explicit scenario inputs; they are not LLM-generated forecasts.", "Discount rate uses a company-specific beta and capital structure with configured market assumptions.", "DCF is one valuation lens and is highly sensitive to discount and terminal-growth assumptions."], **common)
