GROWTH_SIGNALS = [
    "hyper_growth", "high_growth", "moderate_growth", "low_growth", "stagnation", "decline",
    "accelerating_growth", "decelerating_growth", "reacceleration", "consistent_growth", "volatile_growth"
]
PROFITABILITY_SIGNALS = [
    "high_margin_business", "margin_expansion", "margin_contraction", "operating_leverage_present",
    "negative_operating_leverage", "profitability_inflecting_up", "profitability_deteriorating"
]
CASHFLOW_SIGNALS = [
    "strong_cash_generation", "weak_cash_generation", "cash_flow_deterioration", "cash_flow_improving",
    "low_fcf_conversion", "high_fcf_conversion", "earnings_not_backed_by_cash", "cash_flow_exceeds_earnings"
]
BALANCE_SHEET_SIGNALS = [
    "strong_liquidity", "liquidity_stress", "high_leverage", "deleveraging",
    "balance_sheet_strengthening", "balance_sheet_weakening"
]
WORKING_CAPITAL_SIGNALS = [
    "working_capital_build", "working_capital_release", "receivables_pressure", "inventory_build_up",
    "payables_supporting_cash", "cash_conversion_cycle_worsening", "cash_conversion_cycle_improving"
]
EFFICIENCY_SIGNALS = [
    "improving_asset_turnover", "declining_asset_efficiency", "inventory_efficiency_improving", "inventory_efficiency_declining"
]
CAPITAL_ALLOCATION_SIGNALS = [
    "shareholder_friendly", "dilutive_behavior", "buybacks_offset_sbc", "sbc_dilution_not_offset",
    "capex_heavy_growth", "underinvestment_risk"
]
RETURN_SIGNALS = [
    "high_roic", "roic_improving", "roic_declining", "value_creation", "value_destruction"
]
RISK_SIGNALS = [
    "accrual_risk", "liquidity_risk", "leverage_risk", "earnings_quality_concern",
    "one_time_distortion", "unsustainable_growth"
]

SIGNAL_EXPLANATIONS = {
    # Growth Signals
    "hyper_growth": "Extremely rapid revenue growth (>30% YoY). Implies aggressive expansion; check for sustainability and scalability.",
    "high_growth": "Strong revenue growth (15–30% YoY). Indicates a company in a rapid expansion phase.",
    "moderate_growth": "Healthy, sustainable revenue growth (5–15% YoY). Typical of mature but expanding businesses.",
    "low_growth": "Slow revenue growth (0–5% YoY). May indicate market saturation or competitive pressures.",
    "stagnation": "Flat revenue (~0% YoY). Signals a lack of growth; investigate causes.",
    "decline": "Revenue is shrinking (<0% YoY). Red flag; look for structural issues or market loss.",
    "accelerating_growth": "Growth rate is increasing. Indicates positive momentum; check for drivers.",
    "decelerating_growth": "Growth rate is slowing. May signal market saturation or emerging headwinds.",
    "reacceleration": "Growth is picking up after a slowdown. Look for new products, markets, or catalysts.",
    "consistent_growth": "Growth is steady and predictable. Indicates a reliable business model.",
    "volatile_growth": "Growth is erratic or unpredictable. Investigate for cyclical or one-off effects.",

    # Profitability Signals
    "high_margin_business": "Gross or operating margins are high (>50%). Indicates strong pricing power or cost control.",
    "margin_expansion": "Margins are increasing. Suggests improving efficiency or pricing power.",
    "margin_contraction": "Margins are shrinking. Investigate rising costs or pricing pressure.",
    "operating_leverage_present": "Operating income is growing faster than revenue. Indicates scalable cost structure.",
    "negative_operating_leverage": "Operating income is growing slower than revenue. May signal rising fixed costs.",
    "profitability_inflecting_up": "Profitability is improving after a period of weakness. Look for turnaround drivers.",
    "profitability_deteriorating": "Profitability is worsening. Investigate causes and sustainability.",

    # Cash Flow Signals
    "strong_cash_generation": "Operating cash flow is robust. Indicates high-quality earnings.",
    "weak_cash_generation": "Operating cash flow is weak or negative. Red flag for earnings quality.",
    "cash_flow_deterioration": "Cash flow is declining. Investigate for working capital issues or one-offs.",
    "cash_flow_improving": "Cash flow is improving. Positive sign for financial health.",
    "low_fcf_conversion": "Free cash flow is low relative to net income (<0.8x). Indicates accrual risk or high capex.",
    "high_fcf_conversion": "Free cash flow is high relative to net income (>1.2x). May indicate conservative accounting or low reinvestment.",
    "earnings_not_backed_by_cash": "Net income exceeds cash flow. Red flag for aggressive accounting or working capital build.",
    "cash_flow_exceeds_earnings": "Cash flow exceeds net income. Indicates conservative accounting or non-cash charges.",

    # Balance Sheet / Liquidity
    "strong_liquidity": "Current ratio is high (>1.5). Indicates ample short-term resources.",
    "liquidity_stress": "Current ratio is low (<1). Company may struggle to meet short-term obligations.",
    "high_leverage": "Debt levels are high relative to assets or earnings. Increases financial risk.",
    "deleveraging": "Leverage is declining. Indicates risk reduction or improved balance sheet.",
    "balance_sheet_strengthening": "Liquidity or solvency metrics are improving. Positive for creditworthiness.",
    "balance_sheet_weakening": "Liquidity or solvency metrics are deteriorating. Increases risk of distress.",

    # Working Capital Signals
    "working_capital_build": "Increase in working capital. May tie up cash and reduce free cash flow.",
    "working_capital_release": "Decrease in working capital. Frees up cash; may be unsustainable if driven by payables.",
    "receivables_pressure": "Accounts receivable growing faster than revenue. Possible collection issues or aggressive revenue recognition.",
    "inventory_build_up": "Inventory growing faster than revenue. May indicate slowing demand or overproduction.",
    "payables_supporting_cash": "Accounts payable increasing. Company may be delaying payments to suppliers.",
    "cash_conversion_cycle_worsening": "Cash conversion cycle is increasing. Indicates less efficient working capital management.",
    "cash_conversion_cycle_improving": "Cash conversion cycle is decreasing. Indicates more efficient working capital management.",

    # Efficiency Signals
    "improving_asset_turnover": "Asset turnover is rising. Company is using assets more efficiently.",
    "declining_asset_efficiency": "Asset turnover is falling. May indicate underutilized assets.",
    "inventory_efficiency_improving": "Inventory turnover is rising. Indicates better inventory management.",
    "inventory_efficiency_declining": "Inventory turnover is falling. May indicate excess or obsolete inventory.",

    # Capital Allocation Signals
    "shareholder_friendly": "Company is returning capital via buybacks or dividends. Positive for shareholders.",
    "dilutive_behavior": "Share count is rising. Indicates dilution risk.",
    "buybacks_offset_sbc": "Buybacks are sufficient to offset stock-based compensation dilution.",
    "sbc_dilution_not_offset": "Buybacks are insufficient to offset SBC dilution. Shareholders are being diluted.",
    "capex_heavy_growth": "High capex relative to revenue growth. Indicates aggressive reinvestment.",
    "underinvestment_risk": "Capex is declining despite revenue growth. May signal underinvestment in future growth.",

    # Return Signals
    "high_roic": "Return on invested capital is high (>15%). Indicates a high-quality business.",
    "roic_improving": "ROIC is rising. Indicates improving capital efficiency.",
    "roic_declining": "ROIC is falling. May signal deteriorating business quality.",
    "value_creation": "Economic value added is positive. Company is generating returns above its cost of capital.",
    "value_destruction": "Economic value added is negative. Company is destroying value.",

    # Risk Signals
    "accrual_risk": "Earnings are rising while cash flow is falling. High risk of earnings manipulation.",
    "liquidity_risk": "Liquidity metrics are weak. Company may face short-term funding issues.",
    "leverage_risk": "Leverage is high. Increases risk in downturns or rising rates.",
    "earnings_quality_concern": "Low free cash flow conversion or high accruals. Indicates potential earnings quality issues.",
    "one_time_distortion": "High volatility in earnings. May be driven by one-off items.",
    "unsustainable_growth": "Revenue is rising but margins are falling. Growth may not be sustainable.",
}