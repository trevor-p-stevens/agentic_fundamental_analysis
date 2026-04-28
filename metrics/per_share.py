def calculate_per_share_metrics(metrics):
    net_income = metrics.get("net_income")
    shareholders_equity = metrics.get("shareholders_equity")
    revenue = metrics.get("revenue")
    fcf = metrics.get("free_cash_flow")  # Should be calculated elsewhere and passed in
    diluted_shares = metrics.get("shares_diluted")

    def safe_div(n, d):
        try:
            return n / d if n is not None and d not in (None, 0) else None
        except Exception:
            return None

    eps_diluted = safe_div(net_income, diluted_shares)
    bvps = safe_div(shareholders_equity, diluted_shares)
    fcf_per_share = safe_div(fcf, diluted_shares)
    rps = safe_div(revenue, diluted_shares)

    return {
        "eps_diluted": eps_diluted,
        "book_value_per_share": bvps,
        "fcf_per_share": fcf_per_share,
        "revenue_per_share": rps
    }