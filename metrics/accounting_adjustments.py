import pandas as pd

def capitalize_rd(
    df: pd.DataFrame,
    rd_life_years: int = 5,
    rd_col: str = "research_development_expense"
) -> pd.DataFrame:
    df = df.copy().sort_index()
    if rd_col not in df.columns:
        print(f"Warning: {rd_col} not found — skipping R&D capitalization")
        return df

    rd = df[rd_col].fillna(0)
    n  = len(rd)
    rd_asset      = pd.Series(0.0, index=df.index)
    rd_amortization = pd.Series(0.0, index=df.index)

    for i in range(n):
        asset_value = 0.0
        amort_value = 0.0
        for lag in range(rd_life_years):
            if i - lag < 0:
                break
            weight       = (rd_life_years - lag) / rd_life_years
            annual_amort = rd.iloc[i - lag] / rd_life_years
            asset_value += rd.iloc[i - lag] * weight
            amort_value += annual_amort
        rd_asset.iloc[i]       = asset_value
        rd_amortization.iloc[i] = amort_value

    df["rd_asset"]          = rd_asset
    df["rd_amortization"]   = rd_amortization

    tax_rate                = (df["tax_expense"] / df["pretax_income"]).clip(0, 1)
    df["nopat_adjusted"]    = (
        df["operating_income"] + rd * (1 - tax_rate) - rd_amortization * (1 - tax_rate)
    )
    df["invested_capital_adjusted"] = (
        df["shareholders_equity"] + df["total_debt"] - df["cash"] + rd_asset
    )
    df["roic_adjusted"] = df["nopat_adjusted"] / df["invested_capital_adjusted"]
    return df

def capitalize_leases(
    df: pd.DataFrame,
    lease_col: str = "operating_lease_expense",
    discount_rate: float = 0.05
) -> pd.DataFrame:
    df = df.copy()
    if lease_col not in df.columns:
        return df

    lease_debt = df[lease_col] / discount_rate
    df["lease_debt_equivalent"]          = lease_debt
    df["invested_capital_adj_leases"]    = (
        df.get("invested_capital_adjusted", 
               df["shareholders_equity"] + df["total_debt"] - df["cash"])
        + lease_debt
    )
    return df