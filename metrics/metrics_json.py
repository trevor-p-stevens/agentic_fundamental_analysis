import numpy as np
from metrics.metric_categories import METRIC_CATEGORIES
from metrics.deterministic_analysis import (
    classify_trend, trend_strength, compute_confidence
)
from metrics.anomoly_rules import run_all_rules

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
            # anomalies removed from here
        }
        obj["signals"] = get_signals(obj)
        results.append(obj)
    anomalies = run_all_rules(df.iloc[-1].to_dict())
    return {
        "metrics": results,
        "anomalies": anomalies
    }