def calculate_cash_flow_quality(metrics):
    operating_cash_flow = metrics.get("operating_cash_flow")
    capital_expenditures = metrics.get("capex")
    revenue = metrics.get("revenue")
    net_income = metrics.get("net_income")
    current_liabilities = metrics.get("current_liabilities")

    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    # Free Cash Flow (FCF)
    fcf = None
    if operating_cash_flow is not None and capital_expenditures is not None:
        fcf = operating_cash_flow - capital_expenditures

    # FCF Margin
    fcf_margin = safe_div(fcf, revenue) if fcf is not None else None

    # FCF Conversion
    fcf_conversion = safe_div(fcf, net_income) if fcf is not None else None

    # Capex Intensity
    capex_intensity = safe_div(capital_expenditures, revenue)

    # Operating Cash Flow Ratio
    ocf_ratio = safe_div(operating_cash_flow, current_liabilities)

    return {
        "free_cash_flow": fcf,
        "fcf_margin": fcf_margin,
        "fcf_conversion": fcf_conversion,
        "capex_intensity": capex_intensity,
        "operating_cash_flow_ratio": ocf_ratio
    }