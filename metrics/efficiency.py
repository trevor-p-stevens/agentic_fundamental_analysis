import pandas as pd

def calculate_efficiency_metrics(df):
    """
    Expects a DataFrame with columns:
    'revenue', 'total_assets', 'cogs', 'inventory', 'accounts_receivable', 'accounts_payable'
    Returns a DataFrame with efficiency metrics as columns.
    Handles missing or null values gracefully.
    """
    result = pd.DataFrame(index=df.index)

    # Asset Turnover
    result["asset_turnover"] = df["revenue"] / df["total_assets"]

    # Inventory Turnover
    result["inventory_turnover"] = df["cogs"] / df["inventory"]

    # Days Inventory Outstanding (DIO)
    result["days_inventory_outstanding"] = 365 / result["inventory_turnover"]

    # Days Sales Outstanding (DSO)
    result["days_sales_outstanding"] = (df["accounts_receivable"] / df["revenue"]) * 365

    # Days Payable Outstanding (DPO)
    result["days_payable_outstanding"] = (df["accounts_payable"] / df["cogs"]) * 365

    # Cash Conversion Cycle (CCC)
    result["cash_conversion_cycle"] = (
        result["days_inventory_outstanding"]
        + result["days_sales_outstanding"]
        - result["days_payable_outstanding"]
    )

    # Replace inf/-inf with NaN for safe output
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result