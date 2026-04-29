import pandas as pd

def compute_fcf_adjusted(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    fcf_raw = df["operating_cash_flow"] - df["capex"]
    sbc = df.get("sbc", pd.Series(0, index=df.index))
    df["fcf_raw"] = fcf_raw
    df["fcf_adjusted"] = fcf_raw - sbc
    df["sbc_as_pct_fcf"] = sbc / fcf_raw
    return df

def compute_fcfe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    fcf = df["operating_cash_flow"] - df["capex"]
    debt_change = df["total_debt"].diff()
    sbc = df.get("sbc", pd.Series(0, index=df.index))
    interest_exp = df.get("interest_expense", pd.Series(0, index=df.index))
    tax_rate = (df["tax_expense"] / df["pretax_income"]).clip(0, 1)
    df["fcfe"] = (
        fcf
        - interest_exp * (1 - tax_rate)
        + debt_change.fillna(0)
        - sbc
    )
    return df

def compute_shareholder_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    sbc = df.get("sbc", pd.Series(0, index=df.index))
    buybacks = df.get("buybacks", pd.Series(0, index=df.index))
    dividends = df.get("dividends_paid", pd.Series(0, index=df.index))
    fcf = df["operating_cash_flow"] - df["capex"]
    shares_issued = df.get("shares_issued_sbc", pd.Series(0, index=df.index))
    df["net_buybacks"] = buybacks - shares_issued
    df["total_shareholder_return"] = df["net_buybacks"] + dividends
    df["cash_return_pct_fcf"] = df["total_shareholder_return"] / fcf
    df["sbc_pct_net_income"] = sbc / df["net_income"]
    df["net_dilution_cost"] = sbc - df["net_buybacks"]
    return df

def equity_rollforward(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    sbc = df.get("sbc", pd.Series(0, index=df.index))
    buybacks = df.get("buybacks", pd.Series(0, index=df.index))
    dividends = df.get("dividends_paid", pd.Series(0, index=df.index))
    oci = df.get("oci", pd.Series(0, index=df.index))
    equity_change = df["shareholders_equity"].diff()
    df["equity_change_actual"] = equity_change
    df["equity_change_theoretical"] = (
        df["net_income"] + sbc - buybacks - dividends + oci
    )
    df["equity_reconciliation_gap"] = (
        df["equity_change_actual"] - df["equity_change_theoretical"]
    )
    return df

def compute_per_share_adjusted(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    shares = df["shares_diluted"]
    df["share_count_change_yoy"] = shares.pct_change()
    fcf_adjusted = df.get("fcf_adjusted", df["operating_cash_flow"] - df["capex"])
    df["fcf_per_share_adjusted"] = fcf_adjusted / shares
    if "fcfe" in df.columns:
        df["fcfe_per_share"] = df["fcfe"] / shares
    # Market cap and dilution % if share_price is present
    if "share_price" in df.columns:
        df["market_cap"] = df["shares_diluted"] * df["share_price"]
        sbc = df.get("sbc", pd.Series(0, index=df.index))
        net_dilution = df.get("net_dilution_cost", pd.Series(0, index=df.index))
        df["sbc_pct_market_cap"] = sbc / df["market_cap"]
        df["net_dilution_cost_pct_market_cap"] = net_dilution / df["market_cap"]
    return df