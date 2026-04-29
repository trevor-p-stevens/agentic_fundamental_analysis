import pandas as pd


def calculate_cash_flow_quality_metrics(df):
    """
    Expects a DataFrame with columns:
    'operating_cash_flow', 'capex', 'revenue', 'net_income', 'current_liabilities'
    Returns a DataFrame with new cash flow quality metrics as columns.
    """
    result = pd.DataFrame(index=df.index)

    # Free Cash Flow (FCF)
    result["free_cash_flow"] = df["operating_cash_flow"] - df["capex"]

    # FCF Margin
    result["fcf_margin"] = result["free_cash_flow"] / df["revenue"]

    # FCF Conversion
    result["fcf_conversion"] = result["free_cash_flow"] / df["net_income"]

    # Capex Intensity
    result["capex_intensity"] = df["capex"] / df["revenue"]

    # Operating Cash Flow Ratio
    result["operating_cash_flow_ratio"] = df["operating_cash_flow"] / df["current_liabilities"]
    
    # Optionally, replace inf with NaN (e.g., division by zero)
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result