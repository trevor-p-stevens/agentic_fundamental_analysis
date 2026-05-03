CONTRADICTION_FLAG_EXPLANATIONS = {
    "earnings_up_cash_down": "Earnings rising while cash flow declining (accrual risk)",
    "earnings_outpace_cash": "Earnings outpacing cash flow (quality concern)",
    "low_fcf_conversion": "Low FCF conversion (earnings not translating to cash)",
    "receivables_vs_revenue": "Receivables growing faster than revenue (collection risk / channel stuffing)",
    "inventory_vs_revenue": "Inventory growing faster than revenue (demand weakness or overproduction)",
    "payables_vs_revenue": "Payables growing faster than revenue (supplier financing / cash preservation)",
    "margins_up_cash_down": "Margins improving but cash flow deteriorating (possible accounting distortion)",
    "net_income_no_margin": "Net income growing without margin improvement (non-operating drivers)",
    "growth_no_investment": "Revenue growing but capex declining (potential underinvestment)",
    "capex_no_growth": "Capex increasing without revenue growth (poor capital allocation)",
    "buybacks_funded_by_debt": "Buybacks funded by debt (financial engineering risk)",
    "debt_up_cash_flat": "Debt increasing without cash buildup (inefficient capital use)",
    "equity_not_growing": "Equity not increasing despite profits (capital returns or hidden losses)",
    "retained_earnings_mismatch": "Retained earnings mismatch (possible OCI or accounting adjustments)",
    "high_sbc_no_buyback": "High SBC without buyback offset (shareholder dilution)",
    "buybacks_no_offset": "Buybacks not offsetting dilution (ineffective capital return)",
    "capital_up_returns_down": "More capital deployed with lower returns (value destruction)",
    "high_roic_low_capex": "High returns but declining reinvestment (growth sustainability risk)",
    "earnings_up_liquidity_down": "Profitable but liquidity constrained (short-term risk)",
    "cash_up_liquidity_down": "Cash increasing but overall liquidity deteriorating",
    "price_up_earnings_down": "Price increasing despite declining earnings (multiple expansion risk)",
    "price_flat_fundamentals_up": "Fundamentals improving but price stagnant (potential undervaluation)",
    "dividends_exceed_fcf": "Dividends exceed free cash flow (unsustainable payout)",
    "all_metrics_improving": "All metrics improving simultaneously (check for aggressive accounting)",
}

def derive_contradiction_flags(metrics: list[dict]) -> list[dict]:
    m = {x["metric"]: x for x in metrics}
    flags = []

    def val(metric, key="value"):
        return m.get(metric, {}).get(key, None)
    def yoy(metric):
        return m.get(metric, {}).get("yoy", None)
    def trend(metric):
        return m.get(metric, {}).get("trend", None)

    # 1. Earnings vs Cash Flow
    if yoy("net_income") and yoy("net_income") > 0 and yoy("operating_cash_flow") and yoy("operating_cash_flow") < 0:
        flags.append({"flag": "earnings_up_cash_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["earnings_up_cash_down"]})
    if yoy("net_income") is not None and yoy("operating_cash_flow") is not None and yoy("net_income") > yoy("operating_cash_flow") + 0.1:
        flags.append({"flag": "earnings_outpace_cash", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["earnings_outpace_cash"]})
    if val("fcf_raw") is not None and val("net_income") is not None and val("fcf_raw") < val("net_income") * 0.8:
        flags.append({"flag": "low_fcf_conversion", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["low_fcf_conversion"]})

    # 2. Revenue vs Working Capital
    if yoy("accounts_receivable") is not None and yoy("revenue") is not None and yoy("accounts_receivable") > yoy("revenue") + 0.1:
        flags.append({"flag": "receivables_vs_revenue", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["receivables_vs_revenue"]})
    if yoy("inventory") is not None and yoy("revenue") is not None and yoy("inventory") > yoy("revenue") + 0.1:
        flags.append({"flag": "inventory_vs_revenue", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["inventory_vs_revenue"]})
    if yoy("accounts_payable") is not None and yoy("revenue") is not None and yoy("accounts_payable") > yoy("revenue") + 0.15:
        flags.append({"flag": "payables_vs_revenue", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["payables_vs_revenue"]})

    # 3. Profitability vs Cash Behavior
    if trend("gross_margin") == "improving" and yoy("operating_cash_flow") is not None and yoy("operating_cash_flow") < 0:
        flags.append({"flag": "margins_up_cash_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["margins_up_cash_down"]})
    if yoy("net_income") is not None and yoy("net_income") > 0 and trend("operating_margin") != "improving":
        flags.append({"flag": "net_income_no_margin", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["net_income_no_margin"]})

    # 4. Capex vs Growth
    if yoy("revenue") is not None and yoy("revenue") > 0.08 and yoy("capex") is not None and yoy("capex") < 0:
        flags.append({"flag": "growth_no_investment", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["growth_no_investment"]})
    if yoy("capex") is not None and yoy("capex") > 0.15 and yoy("revenue") is not None and yoy("revenue") <= 0:
        flags.append({"flag": "capex_no_growth", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["capex_no_growth"]})

    # 5. Debt vs Cash vs Buybacks
    if val("buybacks") is not None and val("buybacks") > 0 and yoy("total_debt") is not None and yoy("total_debt") > 0 and val("fcf_raw") is not None and val("fcf_raw") < val("buybacks"):
        flags.append({"flag": "buybacks_funded_by_debt", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["buybacks_funded_by_debt"]})
    if yoy("total_debt") is not None and yoy("total_debt") > 0 and yoy("cash") is not None and yoy("cash") <= 0:
        flags.append({"flag": "debt_up_cash_flat", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["debt_up_cash_flat"]})

    # 6. Equity vs Net Income
    if val("net_income") is not None and val("net_income") > 0 and yoy("shareholders_equity") is not None and yoy("shareholders_equity") <= 0:
        flags.append({"flag": "equity_not_growing", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["equity_not_growing"]})
    # Retained earnings mismatch: requires previous period data, so skip for now or implement if available

    # 7. SBC Distortions
    if val("sbc") is not None and val("net_income") is not None and val("sbc") > 0.1 * val("net_income") and val("buybacks") is not None and val("buybacks") < val("sbc"):
        flags.append({"flag": "high_sbc_no_buyback", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["high_sbc_no_buyback"]})
    if val("buybacks") is not None and val("buybacks") > 0 and yoy("shares_diluted") is not None and yoy("shares_diluted") > 0:
        flags.append({"flag": "buybacks_no_offset", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["buybacks_no_offset"]})

    # 8. ROIC / Returns vs Investment
    if yoy("invested_capital") is not None and yoy("invested_capital") > 0 and trend("roic") == "deteriorating":
        flags.append({"flag": "capital_up_returns_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["capital_up_returns_down"]})
    if val("roic") is not None and val("roic") > 0.2 and yoy("capex") is not None and yoy("capex") < 0:
        flags.append({"flag": "high_roic_low_capex", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["high_roic_low_capex"]})

    # 9. Liquidity Contradictions
    if yoy("net_income") is not None and yoy("net_income") > 0 and val("current_ratio") is not None and val("current_ratio") < 1:
        flags.append({"flag": "earnings_up_liquidity_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["earnings_up_liquidity_down"]})
    if yoy("cash") is not None and yoy("cash") > 0 and yoy("current_ratio") is not None and yoy("current_ratio") < 0:
        flags.append({"flag": "cash_up_liquidity_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["cash_up_liquidity_down"]})

    # 10. Market vs Fundamentals
    if yoy("share_price") is not None and yoy("share_price") > 0 and yoy("net_income") is not None and yoy("net_income") < 0:
        flags.append({"flag": "price_up_earnings_down", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["price_up_earnings_down"]})
    if yoy("share_price") is not None and yoy("share_price") <= 0 and yoy("net_income") is not None and yoy("net_income") > 0:
        flags.append({"flag": "price_flat_fundamentals_up", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["price_flat_fundamentals_up"]})

    # 11. FCF vs Dividends
    if val("dividends_paid") is not None and val("fcf_raw") is not None and val("dividends_paid") > val("fcf_raw"):
        flags.append({"flag": "dividends_exceed_fcf", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["dividends_exceed_fcf"]})

    # 12. Too Good to Be True
    if all([
        yoy("revenue") is not None and yoy("revenue") > 0,
        trend("gross_margin") == "improving",
        trend("operating_margin") == "improving",
        yoy("net_income") is not None and yoy("net_income") > 0,
        yoy("operating_cash_flow") is not None and yoy("operating_cash_flow") > 0
    ]):
        flags.append({"flag": "all_metrics_improving", "explanation": CONTRADICTION_FLAG_EXPLANATIONS["all_metrics_improving"]})

    return flags