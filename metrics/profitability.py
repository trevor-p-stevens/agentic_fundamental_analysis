def calculate_profitability(metrics):
    # Required values (should be floats, not None)
    revenue = metrics.get("revenue")
    cogs = metrics.get("cogs")
    operating_income = metrics.get("operating_income")
    net_income = metrics.get("net_income")
    shareholders_equity = metrics.get("shareholders_equity")
    total_assets = metrics.get("total_assets")
    total_debt = metrics.get("total_debt")
    cash = metrics.get("cash")
    depreciation_amortization = metrics.get("depreciation_amortization")
    income_tax_expense = metrics.get("tax_expense")
    pretax_income = metrics.get("pretax_income")

    # Defensive: avoid division by zero or None
    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    # Gross Margin
    gross_margin = safe_div(revenue - cogs, revenue) if revenue and cogs is not None else None

    # Operating Margin
    operating_margin = safe_div(operating_income, revenue)

    # Net Margin
    net_margin = safe_div(net_income, revenue)

    # Return on Equity (ROE)
    roe = safe_div(net_income, shareholders_equity)

    # Return on Assets (ROA)
    roa = safe_div(net_income, total_assets)

    # Tax Rate
    tax_rate = safe_div(income_tax_expense, pretax_income)

    # NOPAT (Net Operating Profit After Tax)
    nopat = operating_income * (1 - tax_rate) if operating_income is not None and tax_rate is not None else None

    # Invested Capital
    invested_capital = None
    if shareholders_equity is not None and total_debt is not None and cash is not None:
        invested_capital = shareholders_equity + total_debt - cash

    # ROIC
    roic = safe_div(nopat, invested_capital) if nopat is not None and invested_capital else None

    # EBITDA and EBITDA Margin
    ebitda = None
    if operating_income is not None and depreciation_amortization is not None:
        ebitda = operating_income + depreciation_amortization
    ebitda_margin = safe_div(ebitda, revenue) if ebitda is not None else None

    return {
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "roe": roe,
        "roa": roa,
        "roic": roic,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "tax_rate": tax_rate,
        "nopat": nopat,
        "invested_capital": invested_capital
    }