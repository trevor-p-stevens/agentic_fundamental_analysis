import pandas as pd

def calculate_solvency_leverage_metrics(df):
    """
    Expects a DataFrame with columns:
    'total_debt', 'shareholders_equity', 'ebitda', 'operating_income', 'interest_expense', 'cash'
    Returns a DataFrame with solvency/leverage metrics as columns.
    Handles missing or null values gracefully.
    """
    result = pd.DataFrame(index=df.index)

    # Debt-to-Equity
    result["debt_to_equity"] = df["total_debt"] / df["shareholders_equity"]

    # Debt-to-EBITDA
    result["debt_to_ebitda"] = df["total_debt"] / df["ebitda"]

    # Interest Coverage Ratio
    result["interest_coverage"] = df["operating_income"] / df["interest_expense"]

    # Net Debt
    result["net_debt"] = df["total_debt"] - df["cash"]

    # Net Debt to EBITDA
    result["net_debt_to_ebitda"] = result["net_debt"] / df["ebitda"]

    # Replace inf/-inf with NaN for safe output
    result = result.replace([float('inf'), float('-inf')], pd.NA)

    return result