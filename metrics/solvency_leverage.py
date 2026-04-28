def calculate_solvency_leverage(metrics):
    total_debt = metrics.get("total_debt")
    shareholders_equity = metrics.get("shareholders_equity")
    ebitda = metrics.get("ebitda")
    operating_income = metrics.get("operating_income")
    interest_expense = metrics.get("interest_expense")
    cash = metrics.get("cash")

    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    # Debt-to-Equity
    debt_to_equity = safe_div(total_debt, shareholders_equity)

    # Debt-to-EBITDA
    debt_to_ebitda = safe_div(total_debt, ebitda)

    # Interest Coverage Ratio
    interest_coverage = safe_div(operating_income, interest_expense)

    # Net Debt
    net_debt = total_debt - cash if total_debt is not None and cash is not None else None

    # Net Debt to EBITDA
    net_debt_to_ebitda = safe_div(net_debt, ebitda) if net_debt is not None else None

    return {
        "debt_to_equity": debt_to_equity,
        "debt_to_ebitda": debt_to_ebitda,
        "interest_coverage": interest_coverage,
        "net_debt": net_debt,
        "net_debt_to_ebitda": net_debt_to_ebitda
    }