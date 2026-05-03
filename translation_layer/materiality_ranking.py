TIER_1 = {
    "revenue": 1.0,
    "net_income": 1.0,
    "eps_diluted": 1.0,
    "free_cash_flow": 1.0,
    "fcf_adjusted": 1.0,
    "fcfe": 1.0,
}
TIER_2 = {
    "gross_margin": 0.95,
    "operating_margin": 0.95,
    "net_margin": 0.95,
    "roic": 0.95,
    "roic_adjusted": 0.95,
    "roe": 0.9,
    "fcf_conversion": 0.95,
    "ebitda_margin": 0.9,
}
TIER_3 = {
    "operating_cash_flow": 0.95,
    "capex": 0.85,
    "capex_intensity": 0.85,
    "buybacks": 0.9,
    "dividends_paid": 0.85,
    "net_buybacks": 0.9,
    "sbc": 0.95,
    "sbc_pct_net_income": 0.95,
    "net_dilution_cost": 0.95,
    "cash_return_pct_fcf": 0.9,
}
TIER_4 = {
    "total_debt": 0.9,
    "net_debt": 0.9,
    "debt_to_equity": 0.9,
    "debt_to_ebitda": 0.9,
    "interest_coverage": 0.9,
    "current_ratio": 0.85,
    "quick_ratio": 0.85,
    "cash_ratio": 0.8,
}
TIER_5 = {
    "accounts_receivable": 0.75,
    "inventory": 0.7,
    "accounts_payable": 0.7,
    "cash_conversion_cycle": 0.85,
    "days_sales_outstanding": 0.8,
    "days_inventory_outstanding": 0.75,
    "days_payable_outstanding": 0.75,
}
TIER_6 = {
    "asset_turnover": 0.7,
    "revenue_per_share": 0.75,
    "fcf_per_share": 0.8,
    "book_value_per_share": 0.75,
    "tax_rate": 0.6,
}
DILUTION = {
    "shares_diluted": 1.0,
    "share_count_change_yoy": 1.0,
    "shares_issued_sbc": 1.0,
    "sbc_pct_market_cap": 0.95,
    "net_dilution_cost_pct_market_cap": 0.95,
}
ADVANCED = {
    "nopat_adjusted": 0.95,
    "invested_capital_adjusted": 0.95,
    "roic_adjusted": 1.0,
    "invested_capital_adj_leases": 0.9,
    "lease_debt_equivalent": 0.9,
}
EQUITY_REALITY = {
    "equity_change_actual": 0.95,
    "equity_change_theoretical": 0.95,
    "equity_reconciliation_gap": 1.0,
    "retained_earnings": 0.9,
}

IMPORTANCE = {
    **TIER_1, **TIER_2, **TIER_3, **TIER_4, **TIER_5, **TIER_6,
    **DILUTION, **ADVANCED, **EQUITY_REALITY,
}