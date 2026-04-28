def calculate_efficiency(metrics):
    revenue = metrics.get("revenue")
    total_assets = metrics.get("total_assets")
    cogs = metrics.get("cogs")
    inventory = metrics.get("inventory")
    accounts_receivable = metrics.get("accounts_receivable")
    accounts_payable = metrics.get("accounts_payable")

    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    # Asset Turnover
    asset_turnover = safe_div(revenue, total_assets)

    # Inventory Turnover
    inventory_turnover = safe_div(cogs, inventory)

    # Days Inventory Outstanding (DIO)
    dio = safe_div(365, inventory_turnover) if inventory_turnover else None

    # Days Sales Outstanding (DSO)
    dso = safe_div(accounts_receivable, revenue) * 365 if accounts_receivable is not None and revenue not in (None, 0) else None

    # Days Payable Outstanding (DPO)
    dpo = safe_div(accounts_payable, cogs) * 365 if accounts_payable is not None and cogs not in (None, 0) else None

    # Cash Conversion Cycle (CCC)
    ccc = dio + dso - dpo if None not in (dio, dso, dpo) else None

    return {
        "asset_turnover": asset_turnover,
        "inventory_turnover": inventory_turnover,
        "days_inventory_outstanding": dio,
        "days_sales_outstanding": dso,
        "days_payable_outstanding": dpo,
        "cash_conversion_cycle": ccc
    }