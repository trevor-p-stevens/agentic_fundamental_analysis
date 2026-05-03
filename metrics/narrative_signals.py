def derive_narrative_signals(metrics: list[dict]) -> list[str]:
    # Build a lookup for easy access
    m = {x["metric"]: x for x in metrics}
    signals = []

    # Helper to get values safely
    def val(metric, key="value"):
        return m.get(metric, {}).get(key, None)

    def yoy(metric):
        return m.get(metric, {}).get("yoy", None)

    # 1. Margin Expansion / Compression
    if yoy("gross_margin") is not None and yoy("gross_margin") > 0:
        signals.append("gross_margin_expanding")
    if (yoy("operating_margin") is not None and yoy("gross_margin") is not None and
        yoy("operating_margin") > yoy("gross_margin")):
        signals.append("operating_leverage")

    # 2. Cost Pressure Signals
    if yoy("cogs") is not None and yoy("revenue") is not None and yoy("cogs") > yoy("revenue"):
        signals.append("cost_pressure")
    if yoy("sga_expense") is not None and yoy("revenue") is not None and yoy("sga_expense") > yoy("revenue"):
        signals.append("overhead_bloat")
    if yoy("research_development_expense") is not None and yoy("revenue") is not None and yoy("research_development_expense") > yoy("revenue"):
        signals.append("investment_phase")

    # 3. Earnings Quality
    if yoy("net_income") is not None and yoy("operating_income") is not None and yoy("net_income") > yoy("operating_income"):
        signals.append("non_operating_boost")
    if yoy("operating_income") is not None and yoy("revenue") is not None and yoy("operating_income") < yoy("revenue"):
        signals.append("margin_pressure")

    # 4. Earnings vs Cash Flow
    if yoy("net_income") and yoy("net_income") > 0 and yoy("operating_cash_flow") and yoy("operating_cash_flow") < 0:
        signals.append("earnings_cash_divergence")
    if val("operating_cash_flow") is not None and val("net_income") is not None and val("operating_cash_flow") < val("net_income"):
        signals.append("low_cash_conversion")

    # 5. Free Cash Flow Dynamics
    if yoy("fcf_raw") is not None and yoy("fcf_raw") < 0 and yoy("operating_cash_flow") is not None and yoy("operating_cash_flow") > 0:
        signals.append("capex_spike")
    if yoy("capex") is not None and yoy("revenue") is not None and yoy("capex") > yoy("revenue"):
        signals.append("heavy_reinvestment")

    # 6. Working Capital Signals
    if yoy("accounts_receivable") is not None and yoy("revenue") is not None and yoy("accounts_receivable") > yoy("revenue"):
        signals.append("receivables_building")
    if yoy("inventory") is not None and yoy("revenue") is not None and yoy("inventory") > yoy("revenue"):
        signals.append("inventory_build")
    if yoy("accounts_payable") is not None and yoy("cogs") is not None and yoy("accounts_payable") < yoy("cogs"):
        signals.append("supplier_financing_declining")

    # 7. Cash Conversion Cycle
    if yoy("cash_conversion_cycle") is not None:
        if yoy("cash_conversion_cycle") > 0:
            signals.append("working_capital_deteriorating")
        elif yoy("cash_conversion_cycle") < 0:
            signals.append("working_capital_improving")

    # 8. Leverage Signals
    if yoy("debt_to_ebitda") is not None and yoy("debt_to_ebitda") > 0:
        signals.append("leverage_increasing")
    if val("net_debt_to_ebitda") is not None and val("net_debt_to_ebitda") < 1:
        signals.append("low_leverage")

    # 9. Liquidity Stress
    if val("current_ratio") is not None and val("current_ratio") < 1:
        signals.append("liquidity_risk")
    if yoy("cash_ratio") is not None and yoy("cash_ratio") < 0 and yoy("total_debt") is not None and yoy("total_debt") > 0:
        signals.append("liquidity_deterioration")

    # 10. SBC + Buyback Interaction
    if val("sbc") is not None and val("sbc") > 0 and val("buybacks") is not None and val("buybacks") > 0:
        net_buybacks = val("buybacks") - val("sbc")
        if net_buybacks < 0:
            signals.append("buybacks_not_offsetting_dilution")
        else:
            signals.append("buybacks_offset_dilution")

    # 11. True Shareholder Return
    if (val("dividends_paid") is not None and val("buybacks") is not None and val("fcf_raw") is not None and
        val("dividends_paid") + val("buybacks") > val("fcf_raw")):
        signals.append("shareholder_returns_debt_funded")

    # 12. Dilution Signals
    if yoy("shares_diluted") is not None and yoy("shares_diluted") > 0:
        signals.append("shareholder_dilution")
    if val("sbc_pct_net_income") is not None and val("sbc_pct_net_income") > 0.2:
        signals.append("high_sbc_burden")

    # 13. Asset Efficiency
    if yoy("asset_turnover") is not None and yoy("asset_turnover") > 0:
        signals.append("efficiency_improving")

    # 14. Return Quality
    if val("roic") is not None and val("roic") > 0.15:
        signals.append("high_return_business")
    if yoy("roic") is not None and yoy("roic") > 0:
        signals.append("returns_improving")

    # 15. High Quality Growth
    if (yoy("revenue") is not None and yoy("revenue") > 0 and
        yoy("operating_margin") is not None and yoy("operating_margin") > 0 and
        val("roic") is not None and val("roic") > 0.15):
        signals.append("high_quality_growth")

    # 16. Fake Growth
    if (yoy("revenue") is not None and yoy("revenue") > 0 and
        yoy("operating_cash_flow") is not None and yoy("operating_cash_flow") < 0):
        signals.append("low_quality_growth")

    # 17. Financial Engineering
    if (yoy("net_income") is not None and yoy("net_income") > 0 and
        yoy("operating_income") is not None and yoy("operating_income") <= 0):
        signals.append("earnings_managed")

    # 18. Underinvestment Risk
    if (yoy("revenue") is not None and yoy("revenue") > 0 and
        yoy("capex") is not None and yoy("capex") < 0):
        signals.append("underinvestment_risk")

    return signals

NARRATIVE_SIGNAL_EXPLANATIONS = {
    "gross_margin_expanding": "Gross margin is increasing, indicating improved profitability from core operations.",
    "operating_leverage": "Operating margin is growing faster than gross margin, showing cost discipline and scalable operations.",
    "cost_pressure": "Cost of goods sold is rising faster than revenue, suggesting margin pressure from input costs.",
    "overhead_bloat": "SG&A expenses are growing faster than revenue, indicating rising overhead or inefficiency.",
    "investment_phase": "R&D expenses are growing faster than revenue, suggesting the company is investing heavily in future growth.",
    "non_operating_boost": "Net income is growing faster than operating income, possibly due to non-operating gains or tax effects.",
    "margin_pressure": "Operating income is growing slower than revenue, indicating margin compression.",
    "earnings_cash_divergence": "Net income is up but operating cash flow is down, a potential red flag for earnings quality.",
    "low_cash_conversion": "Operating cash flow is less than net income, suggesting accruals or weak cash generation.",
    "capex_spike": "Free cash flow is down despite rising operating cash flow, likely due to a spike in capital expenditures.",
    "heavy_reinvestment": "Capex is growing faster than revenue, indicating aggressive reinvestment.",
    "receivables_building": "Accounts receivable are growing faster than revenue, which may signal aggressive revenue recognition or collection issues.",
    "inventory_build": "Inventory is growing faster than revenue, possibly indicating slowing sales or overproduction.",
    "supplier_financing_declining": "Accounts payable are growing slower than COGS, suggesting less supplier financing.",
    "working_capital_deteriorating": "Cash conversion cycle is increasing, indicating less efficient working capital management.",
    "working_capital_improving": "Cash conversion cycle is decreasing, showing improved working capital efficiency.",
    "leverage_increasing": "Debt to EBITDA is rising, indicating increasing leverage.",
    "low_leverage": "Net debt to EBITDA is below 1, showing a conservative balance sheet.",
    "liquidity_risk": "Current ratio is below 1, indicating potential liquidity risk.",
    "liquidity_deterioration": "Cash ratio is declining while debt is increasing, a sign of worsening liquidity.",
    "buybacks_not_offsetting_dilution": "Buybacks are not enough to offset dilution from stock-based compensation.",
    "buybacks_offset_dilution": "Buybacks are sufficient to offset dilution from stock-based compensation.",
    "shareholder_returns_debt_funded": "Dividends and buybacks exceed free cash flow, suggesting returns may be debt-funded.",
    "shareholder_dilution": "Share count is rising, indicating shareholder dilution.",
    "high_sbc_burden": "Stock-based compensation exceeds 20% of net income, a high dilution risk.",
    "efficiency_improving": "Asset turnover is increasing, showing improved efficiency in using assets to generate revenue.",
    "high_return_business": "ROIC exceeds 15%, indicating a high-quality, high-return business.",
    "returns_improving": "ROIC is increasing, showing improving returns on invested capital.",
    "high_quality_growth": "Revenue, operating margin, and ROIC are all rising, indicating high-quality, profitable growth.",
    "low_quality_growth": "Revenue is up but operating cash flow is down, suggesting growth may not be sustainable.",
    "earnings_managed": "Net income is up but operating income is flat or down, a potential sign of earnings management.",
    "underinvestment_risk": "Revenue is up but capex is down, indicating possible underinvestment in the business.",
}