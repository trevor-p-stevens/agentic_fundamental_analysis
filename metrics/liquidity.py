import pandas as pd

def calculate_liquidity_metrics(df):
    """
    Expects a DataFrame with columns:
    'current_assets', 'current_liabilities', 'inventory', 'cash', 'short_term_investments'
    Returns a DataFrame with liquidity metrics as columns.
    Handles missing or null values gracefully.
    """
    result = pd.DataFrame(index=df.index)

    # Current Ratio
    result["current_ratio"] = df["current_assets"] / df["current_liabilities"]

    # Quick Ratio
    result["quick_ratio"] = (df["current_assets"] - df["inventory"]) / df["current_liabilities"]

    # Cash Ratio
    result["cash_ratio"] = (df["cash"].fillna(0) + df["short_term_investments"].fillna(0)) / df["current_liabilities"]

    # Replace inf/-inf with NaN for safe output
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result