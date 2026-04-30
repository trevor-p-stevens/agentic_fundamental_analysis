def earnings_quality_rules(m):
    anomalies = []

    # OCF < Net Income
    if m["operating_cash_flow"] < m["net_income"]:
        anomalies.append({
            "type": "earnings_quality",
            "severity": "high",
            "message": "Operating cash flow below net income (accrual risk)"
        })

    # FCF conversion
    if m["fcf_conversion"] < 0.8:
        anomalies.append({
            "type": "earnings_quality",
            "severity": "medium",
            "message": "Low FCF conversion (<80%)"
        })

    # SBC heavy
    if m["sbc_pct_net_income"] > 0.3:
        anomalies.append({
            "type": "earnings_quality",
            "severity": "high",
            "message": "SBC >30% of net income"
        })

    return anomalies

def balance_sheet_rules(m):
    anomalies = []

    if m["current_ratio"] < 1:
        anomalies.append({
            "type": "liquidity",
            "severity": "high",
            "message": "Current ratio below 1 (liquidity risk)"
        })

    if m["debt_to_equity"] > 2:
        anomalies.append({
            "type": "leverage",
            "severity": "high",
            "message": "High debt to equity (>2)"
        })

    if m["cash"] < m["total_debt"] * 0.2:
        anomalies.append({
            "type": "liquidity",
            "severity": "medium",
            "message": "Low cash relative to debt"
        })

    return anomalies

def growth_rules(m):
    anomalies = []

    if m["revenue_yoy"] < 0:
        anomalies.append({
            "type": "growth",
            "severity": "high",
            "message": "Revenue declining YoY"
        })

    if m["gross_margin_trendslope"] < 0:
        anomalies.append({
            "type": "profitability",
            "severity": "medium",
            "message": "Gross margin deteriorating"
        })

    if m["operating_margin_trendslope"] < 0:
        anomalies.append({
            "type": "profitability",
            "severity": "high",
            "message": "Operating margin deteriorating"
        })

    return anomalies

def shareholder_rules(m):
    anomalies = []

    if m["share_count_change_yoy"] > 0.02:
        anomalies.append({
            "type": "dilution",
            "severity": "high",
            "message": "Share count increasing >2% YoY"
        })

    if m["net_dilution_cost_pct_market_cap"] > 0.02:
        anomalies.append({
            "type": "capital_allocation",
            "severity": "high",
            "message": "High net dilution cost relative to market cap"
        })

    if m["buybacks"] > 0 and m["share_count_change_yoy"] > 0:
        anomalies.append({
            "type": "capital_allocation",
            "severity": "medium",
            "message": "Buybacks not offsetting dilution"
        })

    return anomalies

def run_all_rules(metrics):
    anomalies = []
    anomalies += earnings_quality_rules(metrics)
    anomalies += balance_sheet_rules(metrics)
    anomalies += growth_rules(metrics)
    anomalies += shareholder_rules(metrics)
    return anomalies