import pandas as pd
from metrics.accounting_adjustments import capitalize_leases, capitalize_rd
from metrics.cash_flow_quality import calculate_cash_flow_quality_metrics
from metrics.efficiency import calculate_efficiency_metrics
from metrics.liquidity import calculate_liquidity_metrics
from metrics.per_share import calculate_per_share_metrics
from metrics.profitability import calculate_profitability_metrics
from metrics.solvency_leverage import calculate_solvency_leverage_metrics
import numpy as np
from scipy.stats import linregress
from metrics.retrieve_share_price import get_prices_for_periods
from metrics.equity_adjustments import (
    compute_fcf_adjusted, compute_fcfe, compute_shareholder_returns,
    equity_rollforward, compute_per_share_adjusted
)

def build_dataframe(metrics: dict) -> pd.DataFrame:
    """
    metrics: your metrics_10k or metrics_10q dict
    Returns a DataFrame with period_end as index, each metric as a column.
    """
    series = {}
    for metric, entries in metrics.items():
        s = (
            pd.DataFrame(entries)
            .dropna(subset=["period_end", "value"])
            .set_index("period_end")["value"]
        )
        s.index = pd.to_datetime(s.index)
        series[metric] = s

    df = pd.DataFrame(series).sort_index()
    return df

def detect_trend(series: pd.Series):
    """
    Returns a dict with trend classification, slope, volatility, and consistency (R²).
    """
    s = series.dropna()
    if len(s) < 2:
        return {"trend": None, "slope": None, "volatility": None, "consistency": None}
    x = np.arange(len(s))
    y = s.values
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    trend = "improving" if slope > 0 else "deteriorating"
    volatility = np.std(y)
    consistency = r_value ** 2  # R²
    return {
        "trend": trend,
        "slope": slope,
        "volatility": volatility,
        "consistency": consistency
    }

def trend_detection_layer(df: pd.DataFrame, columns=None):
    """
    For each column in columns (or all numeric columns if None), 
    adds trend, slope, volatility, and consistency as new columns.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns
    trend_data = {}
    for col in columns:
        result = detect_trend(df[col])
        for key, value in result.items():
            suffix = {
                "trend": "trendclass",
                "slope": "trendslope",
                "volatility": "trendvol",
                "consistency": "trendconsistency"
            }[key]
            trend_data.setdefault(f"{col}_{suffix}", []).append(value)
    # Convert to DataFrame (single row, summary for the whole period)
    trend_df = pd.DataFrame(trend_data, index=[df.index[-1]])
    return trend_df

def add_growth_layers(df: pd.DataFrame, freq: str = "auto") -> pd.DataFrame:
    result = df.copy()
    # Infer frequency if needed
    if freq == "auto":
        if len(result.index) > 1:
            delta = (result.index[1] - result.index[0]).days
            if 330 < delta < 400:
                freq = "annual"
            elif 80 < delta < 100:
                freq = "quarterly"
            else:
                freq = "annual"  # fallback
        else:
            freq = "annual"
    periods = 1 if freq == "annual" else 4

    # YoY Growth
    yoy = result.pct_change(periods=periods)
    yoy.columns = [f"{col}_yoy" for col in yoy.columns]
    result = pd.concat([result, yoy], axis=1)

    # Trend Layer
    trend = result.rolling(window=3, min_periods=1).mean()
    trend.columns = [f"{col}_trendmean" for col in trend.columns]
    result = pd.concat([result, trend], axis=1)

    # CAGR calculation for annual data only, and only for original columns
    if freq == "annual":
        n_periods = len(df)
        if n_periods > 1:
            years = n_periods - 1
            cagr_dict = {}
            for col in df.columns:
                series = df[col].dropna()
                if len(series) > 1:
                    start = series.iloc[0]
                    end = series.iloc[-1]
                    if pd.notnull(start) and pd.notnull(end) and start != 0:
                        cagr_dict[f"{col}_cagr"] = (end / start) ** (1 / years) - 1
                    else:
                        cagr_dict[f"{col}_cagr"] = pd.NA
                else:
                    cagr_dict[f"{col}_cagr"] = pd.NA
            # Add CAGR as a single-row DataFrame (last row, or broadcast as needed)
            cagr_df = pd.DataFrame([cagr_dict], index=[df.index[-1]])
            result = pd.concat([result, cagr_df], axis=1)

        N = 5
        result['roe_5yr_avg'] = df['roe'].rolling(window=N, min_periods=1).mean()
        result['roic_5yr_avg'] = df['roic'].rolling(window=N, min_periods=1).mean()
        result['roic_adjusted__5yr_avg'] = df['roic_adjusted'].rolling(window=N, min_periods=1).mean()
    return result


def eval_metrics(df: pd.DataFrame, freq: str = "auto", ticker: str = None) -> pd.DataFrame:
    result = df.copy()

    # --- Add share price if ticker is provided ---
    if ticker is not None:
        period_ends = result.index
        share_prices = get_prices_for_periods(ticker, period_ends)
        result["share_price"] = share_prices.values

    # --- Accounting Adjustments ---
    try:
        rd_life = int(input("Enter R&D useful life in years (e.g., 5): ").strip())
    except Exception:
        rd_life = 5
    result = capitalize_rd(result, rd_life_years=rd_life)
    result = capitalize_leases(result)

    # --- Equity Adjustments ---
    result = compute_fcf_adjusted(result)
    result = compute_fcfe(result)
    result = compute_shareholder_returns(result)
    result = equity_rollforward(result)
    result = compute_per_share_adjusted(result)

    # --- Metric Calculations ---
    cash_flow_df = calculate_cash_flow_quality_metrics(result)
    for col in cash_flow_df.columns:
        result[col] = cash_flow_df[col]
    efficiency_df = calculate_efficiency_metrics(result)
    for col in efficiency_df.columns:
        result[col] = efficiency_df[col]
    liquidity_df = calculate_liquidity_metrics(result)
    for col in liquidity_df.columns:
        result[col] = liquidity_df[col]
    per_share_df = calculate_per_share_metrics(result)
    for col in per_share_df.columns:
        result[col] = per_share_df[col]
    profitability_df = calculate_profitability_metrics(result)
    for col in profitability_df.columns:
        result[col] = profitability_df[col]
    solvency_leverage_df = calculate_solvency_leverage_metrics(result)
    for col in solvency_leverage_df.columns:
        result[col] = solvency_leverage_df[col]

    # --- Growth Layers ---
    result = add_growth_layers(result, freq=freq)

    # --- Trend Detection Layer ---
    trend_df = trend_detection_layer(result)
    result = pd.concat([result, trend_df], axis=1)

    return result

def get_scalar(val):
    if isinstance(val, (pd.Series, np.ndarray)):
        if len(val) == 0:
            return None
        return val.iloc[0] if hasattr(val, "iloc") else val[0]
    return val

def business_quality_score(df: pd.DataFrame, verbose: bool = True) -> int:
    score = 0
    log = []

    # Growth: Revenue CAGR > 10%
    revenue_cagr = get_scalar(df.iloc[-1].get("revenue_cagr", None))
    if revenue_cagr is not None and revenue_cagr > 0.10:
        score += 1
        log.append(f"Growth: Revenue CAGR {revenue_cagr:.2%} > 10% (+1)")
    else:
        log.append(f"Growth: Revenue CAGR {revenue_cagr if revenue_cagr is not None else 'N/A'} <= 10% (+0)")

    # Margins: EBIT (operating) margin trend improving (from trend detection layer)
    ebit_margin_trend = get_scalar(df.iloc[-1].get("operating_margin_trendclass", None))
    if ebit_margin_trend == "improving":
        score += 1
        log.append("Margins: EBIT margin trend improving (+1)")
    else:
        log.append(f"Margins: EBIT margin trend {ebit_margin_trend} (+0)")

    # Returns: 5-year average ROE > 15%
    roe_5yr_avg = get_scalar(df.iloc[-1].get("roe_5yr_avg", None))
    if roe_5yr_avg is not None and roe_5yr_avg > 0.15:
        score += 1
        log.append(f"Returns: 5yr avg ROE {roe_5yr_avg:.2%} > 15% (+1)")
    else:
        log.append(f"Returns: 5yr avg ROE {roe_5yr_avg if roe_5yr_avg is not None else 'N/A'} <= 15% (+0)")

    # Cash: FCF positive and growing (last FCF > 0 and FCF trend improving)
    fcf = get_scalar(df.iloc[-1].get("free_cash_flow", None))
    fcf_trend = get_scalar(df.iloc[-1].get("free_cash_flow_trendclass", None))
    if fcf is not None and fcf > 0 and fcf_trend == "improving":
        score += 1
        log.append("Cash: FCF positive and trend improving (+1)")
    elif fcf is not None and fcf > 0:
        log.append("Cash: FCF positive but trend not improving (+0)")
    else:
        log.append(f"Cash: FCF {fcf if fcf is not None else 'N/A'} not positive (+0)")

    if verbose:
        print("Business Quality Score Breakdown:")
        for line in log:
            print(" -", line)
        print(f"Total Score: {score}/4")

    return score, log

def basic_forecast(
    df: pd.DataFrame,
    years_ahead: int = 3,
    cagr_col: str = "revenue_cagr",
    margin_col: str = "operating_margin",
    tax_col: str = "tax_expense",
    pretax_col: str = "pretax_income",
    shares_col: str = "shares_diluted"
):
    """
    Returns a DataFrame with revenue, EBIT, net income, and EPS forecasts for bull/base/bear scenarios.
    """
    # Get last actuals
    last_revenue = df["revenue"].dropna().iloc[-1]
    last_margin = df[margin_col].dropna().mean()  # mean margin over history
    last_tax_rate = (df[tax_col] / df[pretax_col]).dropna().clip(0, 1).mean()
    last_shares = df[shares_col].dropna().iloc[-1] if shares_col in df.columns else None

    # Get historical CAGR
    base_growth = df[cagr_col].dropna().iloc[-1] if cagr_col in df.columns else 0.0

    # Scenario adjustments
    scenarios = {
        "bull": base_growth + 0.05,
        "base": base_growth,
        "bear": base_growth - 0.05
    }

    forecasts = {}
    for case, growth in scenarios.items():
        forecast = []
        revenue = last_revenue
        for year in range(1, years_ahead + 1):
            revenue = revenue * (1 + growth)
            ebit = revenue * last_margin
            net_income = ebit * (1 - last_tax_rate)
            eps = net_income / last_shares if last_shares else None
            forecast.append({
                "year": df.index[-1].year + year,
                "scenario": case,
                "revenue": revenue,
                "ebit": ebit,
                "net_income": net_income,
                "eps": eps,
                "growth_rate": growth,
                "ebit_margin": last_margin,
                "tax_rate": last_tax_rate,
                "shares_diluted": last_shares
            })
        forecasts[case] = forecast

    # Flatten to DataFrame
    forecast_df = pd.DataFrame([row for case in forecasts for row in forecasts[case]])
    return forecast_df