import pandas as pd

def calculate_per_share_metrics(df):
    """
    Expects a DataFrame with columns:
    'net_income', 'shareholders_equity', 'revenue', 'shares_diluted',
    and either 'free_cash_flow' or both 'operating_cash_flow' and 'capex'.
    """
    result = pd.DataFrame(index=df.index)

    # Compute free cash flow if not present
    if "free_cash_flow" in df.columns:
        fcf = df["free_cash_flow"]
    elif "operating_cash_flow" in df.columns and "capex" in df.columns:
        fcf = df["operating_cash_flow"] - df["capex"]
    else:
        fcf = pd.Series([pd.NA] * len(df), index=df.index)

    # EPS (Diluted)
    result["eps_diluted"] = df["net_income"] / df["shares_diluted"]

    # Book Value Per Share
    result["book_value_per_share"] = df["shareholders_equity"] / df["shares_diluted"]

    # Free Cash Flow Per Share
    result["fcf_per_share"] = fcf / df["shares_diluted"]

    # Revenue Per Share
    result["revenue_per_share"] = df["revenue"] / df["shares_diluted"]

    # Replace inf/-inf with NaN for safe output
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result