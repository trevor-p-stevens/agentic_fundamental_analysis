import pandas as pd

def calculate_profitability_metrics(df):
    """
    Expects a DataFrame with columns:
    'revenue', 'cogs', 'operating_income', 'net_income', 'shareholders_equity',
    'total_assets', 'total_debt', 'cash', 'depreciation_amortization',
    'tax_expense', 'pretax_income'
    Returns a DataFrame with profitability metrics as columns.
    Handles missing or null values gracefully.
    """
    result = pd.DataFrame(index=df.index)

    # Gross Margin
    result["gross_margin"] = (df["revenue"] - df["cogs"]) / df["revenue"]

    # Operating Margin
    result["operating_margin"] = df["operating_income"] / df["revenue"]

    # Net Margin
    result["net_margin"] = df["net_income"] / df["revenue"]

    # Return on Equity (ROE)
    result["roe"] = df["net_income"] / df["shareholders_equity"]

    # Return on Assets (ROA)
    result["roa"] = df["net_income"] / df["total_assets"]

    # Tax Rate
    result["tax_rate"] = df["tax_expense"] / df["pretax_income"]

    # NOPAT (Net Operating Profit After Tax)
    result["nopat"] = df["operating_income"] * (1 - result["tax_rate"])

    # Invested Capital
    result["invested_capital"] = df["shareholders_equity"] + df["total_debt"] - df["cash"]

    # ROIC
    result["roic"] = result["nopat"] / result["invested_capital"]

    # EBITDA
    result["ebitda"] = df["operating_income"] + df["depreciation_amortization"]

    # EBITDA Margin
    result["ebitda_margin"] = result["ebitda"] / df["revenue"]

    # Replace inf/-inf with NaN for safe output
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result