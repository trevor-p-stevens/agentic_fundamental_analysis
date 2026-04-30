METRIC_CATEGORIES = {
    "income_statement": [
        "revenue", "cogs", "gross_profit", "operating_income",
        "interest_expense", "pretax_income", "tax_expense", "net_income",
        "depreciation_amortization", "sbc", "research_development_expense", "sga_expense"
    ],
    "balance_sheet": [
        "cash", "short_term_investments", "accounts_receivable", "inventory",
        "current_assets", "total_assets", "accounts_payable",
        "current_liabilities", "total_debt", "shareholders_equity",
        "retained_earnings"
    ],
    "cash_flow": [
        "operating_cash_flow", "capex", "free_cash_flow",
        "fcf_raw", "fcf_adjusted", "fcfe"
    ],
    "returns": [
        "roe", "roa", "roic", "roic_adjusted"
    ],
    "margins": [
        "gross_margin", "operating_margin", "net_margin", "ebitda_margin", "fcf_margin"
    ],
    "liquidity": [
        "current_ratio", "quick_ratio", "cash_ratio"
    ],
    "efficiency": [
        "asset_turnover", "inventory_turnover",
        "days_inventory_outstanding", "days_sales_outstanding",
        "days_payable_outstanding", "cash_conversion_cycle"
    ],
    "leverage": [
        "debt_to_equity", "debt_to_ebitda", "net_debt_to_ebitda", "interest_coverage"
    ],
    "shareholder": [
        "eps_diluted", "shares_diluted", "buybacks", "dividends_paid",
        "sbc_pct_net_income", "share_count_change_yoy",
        "net_dilution_cost", "total_shareholder_return"
    ]
}