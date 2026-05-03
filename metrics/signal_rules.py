def growth_signals(m):
    signals = []
    yoy = m.get("revenue", {}).get("yoy")
    if yoy is not None:
        if yoy > 0.3:
            signals.append("hyper_growth")
        elif yoy > 0.15:
            signals.append("high_growth")
        elif yoy > 0.05:
            signals.append("moderate_growth")
        elif yoy > 0:
            signals.append("low_growth")
        elif abs(yoy) < 0.01:
            signals.append("stagnation")
        else:
            signals.append("decline")
        # Acceleration
        if m.get("revenue", {}).get("trend_slope", 0) > 0 and yoy > m.get("revenue", {}).get("trend_strength", 0):
            signals.append("accelerating_growth")
        if m.get("revenue", {}).get("trend_slope", 0) < 0 and yoy < m.get("revenue", {}).get("trend_strength", 0):
            signals.append("decelerating_growth")
        if m.get("revenue", {}).get("trend_slope", 0) > 0 and m.get("revenue", {}).get("trend_strength", 0) < 0:
            signals.append("reacceleration")
        if m.get("revenue", {}).get("trend_consistency", 0) > 0.8:
            signals.append("consistent_growth")
        if m.get("revenue", {}).get("trend_volatility", 0) > 0.2:
            signals.append("volatile_growth")
    return signals

def margin_signals(m):
    signals = []
    if m.get("gross_profit", {}).get("yoy") is not None and m.get("revenue", {}).get("yoy") is not None:
        if m["gross_profit"]["yoy"] > m["revenue"]["yoy"]:
            signals.append("margin_expansion")
        elif m["gross_profit"]["yoy"] < m["revenue"]["yoy"]:
            signals.append("margin_contraction")
    if m.get("operating_income", {}).get("yoy") is not None and m.get("revenue", {}).get("yoy") is not None:
        if m["operating_income"]["yoy"] > m["revenue"]["yoy"]:
            signals.append("operating_leverage_present")
        elif m["operating_income"]["yoy"] < m["revenue"]["yoy"]:
            signals.append("negative_operating_leverage")
    if m.get("gross_margin", {}).get("trend_slope", 0) > 0:
        signals.append("profitability_inflecting_up")
    if m.get("gross_margin", {}).get("trend_slope", 0) < 0:
        signals.append("profitability_deteriorating")
    if m.get("gross_margin", {}).get("value", 0) > 0.5:
        signals.append("high_margin_business")
    return signals

def cashflow_signals(m):
    signals = []
    ni = m.get("net_income", {}).get("value")
    ocf = m.get("operating_cash_flow", {}).get("value")
    fcf = m.get("free_cash_flow", {}).get("value")
    if ni is not None and ocf is not None:
        if ocf > ni:
            signals.append("cash_flow_exceeds_earnings")
        elif ocf < ni:
            signals.append("earnings_not_backed_by_cash")
    fcf_conv = m.get("fcf_conversion", {}).get("value")
    if fcf_conv is not None:
        if fcf_conv < 0.8:
            signals.append("low_fcf_conversion")
        elif fcf_conv > 1.2:
            signals.append("high_fcf_conversion")
    if m.get("free_cash_flow", {}).get("yoy", 0) < 0:
        signals.append("cash_flow_deterioration")
    if m.get("free_cash_flow", {}).get("yoy", 0) > 0:
        signals.append("cash_flow_improving")
    if ocf is not None and ocf > 0:
        signals.append("strong_cash_generation")
    if ocf is not None and ocf < 0:
        signals.append("weak_cash_generation")
    return signals

def balance_sheet_signals(m):
    signals = []
    cr = m.get("current_ratio", {}).get("value")
    qr = m.get("quick_ratio", {}).get("value")
    cash_ratio = m.get("cash_ratio", {}).get("value")
    debt = m.get("total_debt", {}).get("value")
    net_debt = m.get("net_debt", {}).get("value")
    debt_to_ebitda = m.get("debt_to_ebitda", {}).get("value")
    if cr is not None and cr > 1.5:
        signals.append("strong_liquidity")
    if cr is not None and cr < 1:
        signals.append("liquidity_stress")
    if debt is not None and debt > 0.7 * (m.get("total_assets", {}).get("value") or 1):
        signals.append("high_leverage")
    if debt_to_ebitda is not None and debt_to_ebitda > 3:
        signals.append("high_leverage")
    if debt_to_ebitda is not None and debt_to_ebitda < 2:
        signals.append("deleveraging")
    # Trend-based
    if m.get("current_ratio", {}).get("trend_slope", 0) > 0:
        signals.append("balance_sheet_strengthening")
    if m.get("current_ratio", {}).get("trend_slope", 0) < 0:
        signals.append("balance_sheet_weakening")
    return signals

def working_capital_signals(m):
    signals = []
    if m.get("accounts_receivable", {}).get("yoy") is not None and m.get("revenue", {}).get("yoy") is not None:
        if m["accounts_receivable"]["yoy"] > m["revenue"]["yoy"]:
            signals.append("receivables_pressure")
    if m.get("inventory", {}).get("yoy") is not None and m.get("revenue", {}).get("yoy") is not None:
        if m["inventory"]["yoy"] > m["revenue"]["yoy"]:
            signals.append("inventory_build_up")
    if m.get("accounts_payable", {}).get("trend_slope", 0) > 0:
        signals.append("payables_supporting_cash")
    if m.get("cash_conversion_cycle", {}).get("trend_slope", 0) > 0:
        signals.append("cash_conversion_cycle_worsening")
    if m.get("cash_conversion_cycle", {}).get("trend_slope", 0) < 0:
        signals.append("cash_conversion_cycle_improving")
    return signals

def efficiency_signals(m):
    signals = []
    at = m.get("asset_turnover", {}).get("value")
    if at is not None and at > 1:
        signals.append("improving_asset_turnover")
    if at is not None and at < 0.7:
        signals.append("declining_asset_efficiency")
    if m.get("inventory_turnover", {}).get("trend_slope", 0) > 0:
        signals.append("inventory_efficiency_improving")
    if m.get("inventory_turnover", {}).get("trend_slope", 0) < 0:
        signals.append("inventory_efficiency_declining")
    return signals

def capital_allocation_signals(m):
    signals = []
    sbc = m.get("sbc", {}).get("value")
    buybacks = m.get("buybacks", {}).get("value")
    if buybacks is not None and sbc is not None:
        if buybacks > sbc:
            signals.append("buybacks_offset_sbc")
        else:
            signals.append("sbc_dilution_not_offset")
    if m.get("capex", {}).get("yoy", 0) > 0.15 and m.get("revenue", {}).get("yoy", 0) > 0.05:
        signals.append("capex_heavy_growth")
    if m.get("capex", {}).get("yoy", 0) < 0 and m.get("revenue", {}).get("yoy", 0) > 0.05:
        signals.append("underinvestment_risk")
    # Shareholder friendly: high buybacks or dividends
    if (buybacks or 0) > 0 or (m.get("dividends_paid", {}).get("value") or 0) > 0:
        signals.append("shareholder_friendly")
    # Dilutive behavior: shares_diluted increasing
    if m.get("shares_diluted", {}).get("yoy", 0) > 0:
        signals.append("dilutive_behavior")
    return signals

def return_signals(m):
    signals = []
    roic = m.get("roic", {}).get("value")
    roic_yoy = m.get("roic", {}).get("yoy")
    if roic is not None:
        if roic > 0.15:
            signals.append("high_roic")
        if roic_yoy is not None and roic_yoy > 0:
            signals.append("roic_improving")
        if roic_yoy is not None and roic_yoy < 0:
            signals.append("roic_declining")
    if m.get("economic_value_added", {}).get("value", 0) > 0:
        signals.append("value_creation")
    if m.get("economic_value_added", {}).get("value", 0) < 0:
        signals.append("value_destruction")
    return signals

def risk_signals(m):
    signals = []
    # Accrual risk: net income up, cash flow down
    ni_yoy = m.get("net_income", {}).get("yoy")
    ocf_yoy = m.get("operating_cash_flow", {}).get("yoy")
    if ni_yoy is not None and ocf_yoy is not None and ni_yoy > 0 and ocf_yoy < 0:
        signals.append("accrual_risk")
    # Liquidity risk
    if m.get("current_ratio", {}).get("value", 1) < 1:
        signals.append("liquidity_risk")
    # Leverage risk
    if m.get("debt_to_ebitda", {}).get("value", 0) > 3:
        signals.append("leverage_risk")
    # Earnings quality concern: low fcf conversion
    if m.get("fcf_conversion", {}).get("value", 1) < 0.8:
        signals.append("earnings_quality_concern")
    # One-time distortion: high volatility in net income
    if m.get("net_income", {}).get("trend_volatility", 0) > 0.3:
        signals.append("one_time_distortion")
    # Unsustainable growth: revenue up, margins down
    if ni_yoy is not None and ni_yoy > 0 and m.get("gross_margin", {}).get("trend_slope", 0) < 0:
        signals.append("unsustainable_growth")
    return signals

def derive_advanced_signals(metrics: list[dict]) -> list[str]:
    m = {x["metric"]: x for x in metrics}
    signals = []
    signals += growth_signals(m)
    signals += margin_signals(m)
    signals += cashflow_signals(m)
    signals += balance_sheet_signals(m)
    signals += working_capital_signals(m)
    signals += efficiency_signals(m)
    signals += capital_allocation_signals(m)
    signals += return_signals(m)
    signals += risk_signals(m)
    return signals