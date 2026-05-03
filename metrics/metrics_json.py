import numpy as np
from metrics.contradictions import derive_contradiction_flags
from metrics.metric_categories import METRIC_CATEGORIES
from metrics.deterministic_analysis import (
    classify_trend, trend_strength, compute_confidence
)
from metrics.anomoly_rules import run_all_rules
from metrics.narrative_signals import derive_narrative_signals
from metrics.signal_rules import derive_advanced_signals
from metrics.signal_rules import derive_advanced_signals, growth_signals, margin_signals, cashflow_signals, balance_sheet_signals, working_capital_signals, efficiency_signals, capital_allocation_signals, return_signals, risk_signals
import math

def safe_get(df, col, default=np.nan):
    return df[col].iloc[-1] if col in df.columns else default

def get_signals(metric_obj):
    signals = []
    if metric_obj["yoy"] is not None and metric_obj["yoy"] > 0:
        signals.append("positive_growth")
    if metric_obj["trend_consistency"] is not None and metric_obj["trend_consistency"] > 0.7:
        signals.append("consistent_growth")
    if metric_obj["trend_volatility"] is not None and metric_obj["trend_volatility"] < 0.2:
        signals.append("low_volatility")
    return signals

def to_serializable(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    if isinstance(val, (np.bool_)):
        return bool(val)
    if val is np.nan or val is None:
        return None
    return val

def clean_metric(m: dict) -> dict:
    """Replace NaN/Inf with None before briefing or LLM ingestion."""
    for key in ["yoy", "cagr", "trend_slope", "trend_strength", "trend_volatility"]:
        val = m.get(key)
        if val is None:
            continue
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            m[key] = None
    return m

def canonical_metrics_json(df):
    results = []
    category_lookup = {m: cat for cat, metrics in METRIC_CATEGORIES.items() for m in metrics}
    for metric in category_lookup:
        obj = {
            "metric": metric,
            "value": to_serializable(safe_get(df, metric, None)),
            "yoy": to_serializable(safe_get(df, f"{metric}_yoy", None)),
            "cagr": to_serializable(safe_get(df, f"{metric}_cagr", None)),
            "trend": to_serializable(classify_trend(
                safe_get(df, f"{metric}_trendslope"),
                safe_get(df, f"{metric}_trendconsistency"),
                safe_get(df, f"{metric}_trendvol")
            )),
            "trend_strength": to_serializable(trend_strength(
                safe_get(df, f"{metric}_trendslope"),
                safe_get(df, f"{metric}_trendconsistency")
            )),
            "trend_slope": to_serializable(safe_get(df, f"{metric}_trendslope", None)),
            "trend_consistency": to_serializable(safe_get(df, f"{metric}_trendconsistency", None)),
            "trend_volatility": to_serializable(safe_get(df, f"{metric}_trendvol", None)),
            "category": category_lookup[metric],
            "confidence": to_serializable(compute_confidence({
                "trendconsistency": safe_get(df, f"{metric}_trendconsistency", 0),
                "trendvol": safe_get(df, f"{metric}_trendvol", 1),
                "trendslope": safe_get(df, f"{metric}_trendslope", 0),
                "data_points": df[metric].count() if metric in df.columns else 0
            })),
        }
        # Attach per-metric signals
        m_dict = {x["metric"]: x for x in results + [obj]}
        if metric in m_dict:
            # You can expand this to use the right group for each metric
            sigs = []
            sigs += growth_signals(m_dict) if metric == "revenue" else []
            sigs += margin_signals(m_dict) if metric in ["gross_profit", "operating_income", "gross_margin"] else []
            sigs += cashflow_signals(m_dict) if metric in ["net_income", "operating_cash_flow", "free_cash_flow"] else []
            sigs += balance_sheet_signals(m_dict) if metric in ["current_ratio", "total_debt"] else []
            sigs += working_capital_signals(m_dict) if metric in ["accounts_receivable", "inventory", "accounts_payable", "cash_conversion_cycle"] else []
            sigs += efficiency_signals(m_dict) if metric in ["asset_turnover", "inventory_turnover"] else []
            sigs += capital_allocation_signals(m_dict) if metric in ["sbc", "buybacks", "capex", "dividends_paid", "shares_diluted"] else []
            sigs += return_signals(m_dict) if metric in ["roic", "economic_value_added"] else []
            sigs += risk_signals(m_dict) if metric in ["net_income", "operating_cash_flow", "debt_to_ebitda", "fcf_conversion"] else []
            obj["signals"] = list(set(sigs))
        else:
            obj["signals"] = []
        results.append(clean_metric(obj))
    anomalies = run_all_rules(df.iloc[-1].to_dict())
    advanced_signals = derive_advanced_signals(results)
    contradiction_flags = derive_contradiction_flags(results)
    return {
        "metrics": results,
        "anomalies": anomalies,
        "advanced_signals": advanced_signals,
        "contradiction_flags": contradiction_flags,
    }