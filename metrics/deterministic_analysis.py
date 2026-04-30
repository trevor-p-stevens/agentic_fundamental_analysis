from metrics.anomoly_rules import run_all_rules

def analyze_metric(metric_name, df):
    # Assume df is your metrics DataFrame, with trend columns, etc.
    last_idx = df.index[-1]
    metric = {
        "metric": metric_name,
        "trend": classify_trend(
            df[f"{metric_name}_trendslope"].iloc[-1],
            df[f"{metric_name}_trendconsistency"].iloc[-1],
            df[f"{metric_name}_trendvol"].iloc[-1]
        ),
        "trend_strength": trend_strength(
            df[f"{metric_name}_trendslope"].iloc[-1],
            df[f"{metric_name}_trendconsistency"].iloc[-1]
        ),
        "confidence": compute_confidence({
            "trendconsistency": df[f"{metric_name}_trendconsistency"].iloc[-1],
            "trendvol": df[f"{metric_name}_trendvol"].iloc[-1],
            "trendslope": df[f"{metric_name}_trendslope"].iloc[-1],
            "data_points": df[metric_name].count()
        }),
        "anomalies": run_all_rules(df.loc[last_idx].to_dict()),
        "interpretation_hint": "growth positive" if df[f"{metric_name}_trendslope"].iloc[-1] > 0 else "growth negative"
    }
    return metric

def classify_trend(slope, consistency, volatility):
    if consistency < 0.3:
        return "noisy"

    if slope > 0:
        if volatility < 0.2:
            return "strong_uptrend"
        return "weak_uptrend"

    if slope < 0:
        if volatility < 0.2:
            return "strong_downtrend"
        return "weak_downtrend"

    return "flat"

def trend_strength(slope, consistency):
    return abs(slope) * consistency

def compute_confidence(metric):
    score = 0

    if metric.get("trendconsistency", 0) > 0.7:
        score += 1

    if metric.get("trendvol", 1) < 0.3:
        score += 1

    if abs(metric.get("trendslope", 0)) > 0:
        score += 1

    if metric.get("data_points", 0) >= 4:
        score += 1

    if score >= 3:
        return "HIGH"
    elif score == 2:
        return "MEDIUM"
    return "LOW"