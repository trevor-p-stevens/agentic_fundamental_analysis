from typing import List, Dict
from metrics.contradictions import CONTRADICTION_FLAG_EXPLANATIONS
from metrics.narrative_signals import NARRATIVE_SIGNAL_EXPLANATIONS
from metrics.signal_taxonomy import SIGNAL_EXPLANATIONS
from metrics.narrative_signals import NARRATIVE_SIGNAL_EXPLANATIONS, derive_narrative_signals
from metrics.signal_taxonomy import SIGNAL_EXPLANATIONS
from translation_layer.materiality_ranking import IMPORTANCE

MATERIALITY_WEIGHTS = {
    "income_statement": 1.0,
    "cash_flow":        0.95,
    "balance_sheet":    0.85,
    "efficiency":       0.75,
    "per_share":        0.70,
}

SIGNAL_SEVERITY = {
    "negative_growth":        0.8,
    "declining_margins":      0.9,
    "inconsistent_growth":    0.6,
    "positive_growth":        0.3,
    "consistent_growth":      0.2,
}

def adjust_importance(metric, value, anomalies):
    base = IMPORTANCE.get(metric, 0.5)
    # Boost if anomaly-related
    if any(metric in a.get("message", "").lower() for a in anomalies):
        base += 0.1
    # Boost if extreme YoY movement
    if isinstance(value, dict) and abs(value.get("yoy", 0) or 0) > 0.2:
        base += 0.05
    return min(base, 1.2)

def prioritize_metrics(metrics: List[Dict], anomalies: List[Dict] = None) -> Dict:
    if anomalies is None:
        anomalies = []
    groups = {}
    for m in metrics:
        cat = m["category"]
        if cat not in groups:
            groups[cat] = []
        # Compute priority score
        signal_score = max(
            (SIGNAL_SEVERITY.get(s, 0.1) for s in m.get("signals", [])),
            default=0.1
        )
        confidence_score = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}.get(
            m["confidence"], 0.5
        )
        # Use context-aware importance
        materiality = adjust_importance(m["metric"], m, anomalies)
        m["priority_score"] = round(
            signal_score * confidence_score * materiality, 3
        )
        groups[cat].append(m)
    for cat in groups:
        groups[cat].sort(key=lambda x: x["priority_score"], reverse=True)
    return groups

def build_anomaly_brief(anomalies: List[Dict]) -> Dict:
    return {
        "high":   [a for a in anomalies if a["severity"] == "high"],
        "medium": [a for a in anomalies if a["severity"] == "medium"],
        "low":    [a for a in anomalies if a["severity"] == "low"],
    }

from metrics.narrative_signals import NARRATIVE_SIGNAL_EXPLANATIONS, derive_narrative_signals
from metrics.contradictions import derive_contradiction_flags  # <-- Add this import

def build_llm_briefing(
    grouped_metrics: Dict,
    anomaly_brief: Dict,
    ticker: str,
    all_metrics: List[Dict] = None,
    advanced_signals: list = None  # <-- Add this argument
) -> str:
    lines = [f"FINANCIAL BRIEFING: {ticker}\n"]

    # ── Advanced Signals Section ────────────────────────────────
    if advanced_signals:
        lines.append("=== ADVANCED ECONOMIC SIGNALS ===")
        for sig in advanced_signals:
            explanation = SIGNAL_EXPLANATIONS.get(sig, "")
            lines.append(f"- {sig}: {explanation}")
        lines.append("")

    # ── Narrative Signals Section ────────────────────────────────
    if all_metrics is not None:
        narrative_signals = derive_narrative_signals(all_metrics)
        if narrative_signals:
            lines.append("=== CROSS-METRIC NARRATIVE SIGNALS ===")
            for sig in narrative_signals:
                explanation = NARRATIVE_SIGNAL_EXPLANATIONS.get(sig, "")
                lines.append(f"- {sig}: {explanation}")
            lines.append("")

        # ── Contradiction Flags Section ─────────────────────────────
        contradiction_flags = derive_contradiction_flags(all_metrics)
        if contradiction_flags:
            lines.append("=== CONTRADICTION FLAGS (potential red flags) ===")
            for flag in contradiction_flags:
                lines.append(f"- {flag['flag']}: {flag['explanation']}")
            lines.append("")

    # ── Critical anomalies first ────────────────────────────────
    if anomaly_brief["high"]:
        lines.append("=== CRITICAL FLAGS (investigate first) ===")
        for a in anomaly_brief["high"]:
            lines.append(f"[{a['type'].upper()}] {a['message']}")
        lines.append("")
        
    GROUP_ORDER = [
        "income_statement",
        "cash_flow",
        "balance_sheet",
        "efficiency",
        "per_share",
    ]
    for cat in GROUP_ORDER:
        metrics = grouped_metrics.get(cat, [])
        if not metrics:
            continue
        lines.append(f"=== {cat.upper().replace('_', ' ')} ===")
        for m in metrics:
            yoy_val = m.get('yoy')
            cagr_val = m.get('cagr')
            yoy_str  = f"{yoy_val:+.1%}" if isinstance(yoy_val, (int, float)) and yoy_val is not None else "N/A"
            cagr_str = f"{cagr_val:+.1%}" if isinstance(cagr_val, (int, float)) and cagr_val is not None else "N/A"
            flags = ""
            if m["priority_score"] > 0.6:
                flags = " ⚠ HIGH PRIORITY"
            elif m["priority_score"] > 0.35:
                flags = " — NOTABLE"
            # Show signals
            signal_strs = []
            for sig in m.get("signals", []):
                expl = SIGNAL_EXPLANATIONS.get(sig, sig)
                signal_strs.append(f"{sig} ({expl})")
            lines.append(
                f"  {m['metric']:35s} "
                f"YoY: {yoy_str:>8}  "
                f"CAGR: {cagr_str:>8}  "
                f"Trend: {m['trend']:20s}  "
                f"Signals: {', '.join(signal_strs)}"
                f"{flags}"
            )
        lines.append("")
    if anomaly_brief["medium"]:
        lines.append("=== SECONDARY FLAGS ===")
        for a in anomaly_brief["medium"]:
            lines.append(f"[{a['type'].upper()}] {a['message']}")
    return "\n".join(lines)


from dataclasses import dataclass, field
from typing import Literal

@dataclass
class BriefingItem:
    id:          str
    category:    Literal[
                     "critical_flag",
                     "contradiction",
                     "narrative_signal",
                     "metric"
                 ]
    priority:    int                    # 1 = highest
    subject:     str                    # signal name or metric name
    data:        dict                   # all fields relevant to this item
    definition:  str = ""               # the signal definition inline


def briefing_to_items(
    grouped_metrics: Dict,
    anomaly_brief: Dict,
    ticker: str,
    all_metrics: List[Dict] = None,
    advanced_signals: list = None
) -> list[BriefingItem]:
    """
    Converts the same inputs as build_llm_briefing into an ordered list of BriefingItems.
    Priority order: advanced_signals → narrative_signals → contradiction_flags → critical_flags → metrics
    """
    items = []
    counter = 0

    # 1. Advanced signals
    if advanced_signals:
        for sig in advanced_signals:
            items.append(BriefingItem(
                id=f"bi_{counter}",
                category="narrative_signal",
                priority=0,
                subject=sig,
                data={
                    "explanation": SIGNAL_EXPLANATIONS.get(sig, ""),
                },
                definition=SIGNAL_EXPLANATIONS.get(sig, ""),
            ))
            counter += 1

    # 2. Narrative signals and contradiction flags (from all_metrics)
    if all_metrics is not None:
        from metrics.narrative_signals import derive_narrative_signals
        from metrics.contradictions import derive_contradiction_flags

        narrative_signals = derive_narrative_signals(all_metrics)
        for sig in narrative_signals:
            items.append(BriefingItem(
                id=f"bi_{counter}",
                category="narrative_signal",
                priority=1,
                subject=sig,
                data={
                    "explanation": NARRATIVE_SIGNAL_EXPLANATIONS.get(sig, ""),
                },
                definition=NARRATIVE_SIGNAL_EXPLANATIONS.get(sig, ""),
            ))
            counter += 1

        contradiction_flags = derive_contradiction_flags(all_metrics)
        for flag in contradiction_flags:
            items.append(BriefingItem(
                id=f"bi_{counter}",
                category="contradiction",
                priority=2,
                subject=flag["flag"],
                data={
                    "explanation": flag["explanation"],
                },
                definition=flag["explanation"],
            ))
            counter += 1

    # 3. Critical anomalies
    for a in anomaly_brief.get("high", []):
        items.append(BriefingItem(
            id=f"bi_{counter}",
            category="critical_flag",
            priority=3,
            subject=a["type"],
            data={
                "message":  a["message"],
                "severity": a["severity"],
            },
        ))
        counter += 1

    # 4. Metrics (flattened from grouped_metrics, sorted by priority_score)
    all_metrics_flat = []
    for cat in grouped_metrics:
        all_metrics_flat.extend(grouped_metrics[cat])
    sorted_metrics = sorted(
        all_metrics_flat,
        key=lambda m: m.get("priority_score", 0),
        reverse=True
    )
    for m in sorted_metrics:
        items.append(BriefingItem(
            id=f"bi_{counter}",
            category="metric",
            priority=4,
            subject=m["metric"],
            data={
                "value":       m.get("value"),
                "yoy":         m.get("yoy"),
                "cagr":        m.get("cagr"),
                "trend":       m.get("trend"),
                "signals":     m.get("signals", []),
                "confidence":  m.get("confidence"),
                "category":    m.get("category"),
            },
            definition=build_metric_definition(m),
        ))
        counter += 1

    return items


def build_metric_definition(m: dict) -> str:
    """Inline definition for signals present on this metric."""
    if not m.get("signals"):
        return ""
    lines = []
    for s in m["signals"]:
        defn = SIGNAL_EXPLANATIONS.get(s)
        if defn:
            lines.append(f"{s}: {defn}")
    return " | ".join(lines)