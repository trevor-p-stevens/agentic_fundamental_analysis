def calculate_liquidity(metrics):
    current_assets = metrics.get("current_assets")
    current_liabilities = metrics.get("current_liabilities")
    inventory = metrics.get("inventory")
    cash = metrics.get("cash")
    short_term_investments = metrics.get("short_term_investments")

    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    # Current Ratio
    current_ratio = safe_div(current_assets, current_liabilities)

    # Quick Ratio
    quick_ratio = safe_div(
        current_assets - inventory if current_assets is not None and inventory is not None else None,
        current_liabilities
    )

    # Cash Ratio
    cash_ratio = safe_div(
        (cash if cash is not None else 0) + (short_term_investments if short_term_investments is not None else 0),
        current_liabilities
    )

    return {
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "cash_ratio": cash_ratio
    }