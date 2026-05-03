from analysis.nodes.briefing import parse_json
from ..config import llm
from ..state import AnalysisState
from ..prompts import HYPOTHESIS_TEST_PROMPT, SYSTEM_PROMPT
from datetime import datetime
import json


def hypothesis_evaluation_node(state: AnalysisState) -> dict:
    """
    After each research iteration, evaluate which hypotheses
    now have enough evidence to conclude.
    """
    log_entries = []
    updated = []

    for h in state["hypotheses"]:
        print("Evaluating Hypothesis:", h, flush=True)

        # Already decided in a prior iteration
        if h.get("status") != "open":
            updated.append(h)
            continue

        has_for = len(h.get("evidence_for", [])) > 0
        has_against = len(h.get("evidence_against", [])) > 0

        # If no evidence yet, only keep open while linked research is still pending.
        if not has_for and not has_against:
            pending_for_h = any(
                q.get("hypothesis_id") == h.get("id") and q.get("status") == "pending"
                for q in state.get("research_queue", [])
            )

            if pending_for_h:
                updated.append(h)
                continue

            # No evidence and no pending linked work: close as inconclusive.
            h["status"] = "inconclusive"
            h["confidence"] = 0.0
            h["conclusion"] = (
                "Research completed with insufficient direct evidence to confirm or reject this hypothesis."
            )
            h["implication"] = (
                "Treat this thesis as unresolved; require additional targeted evidence before using it in decisions."
            )
            updated.append(h)

            log_entries.append({
                "node": "hypothesis_evaluation",
                "type": "judgment",
                "subject": h["id"],
                "content": f"{h['statement']} -> INCONCLUSIVE\n{h['conclusion']}",
                "confidence": h["confidence"],
                "evidence": [],
                "implication": h["implication"],
                "timestamp": datetime.now().isoformat(),
            })
            continue

        # Evidence exists: run model-based hypothesis evaluation.
        prompt = HYPOTHESIS_TEST_PROMPT.format(
            statement=h["statement"],
            evidence_for=json.dumps(h.get("evidence_for", []), indent=2),
            evidence_against=json.dumps(h.get("evidence_against", []), indent=2),
            related_findings=json.dumps([
                l for l in state["log"]
                if l.get("hypothesis_id") == h["id"]
            ], indent=2),
        )

        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        result = parse_json(response.content)

        h["status"] = result.get("status", "inconclusive")
        h["confidence"] = result.get("confidence", 0.0)
        h["conclusion"] = result.get("conclusion", "")
        h["implication"] = result.get("implication", "")
        updated.append(h)

        log_entries.append({
            "node": "hypothesis_evaluation",
            "type": "judgment",
            "subject": h["id"],
            "content": f"{h['statement']} -> {h['status'].upper()}\n{h['conclusion']}",
            "confidence": h["confidence"],
            "evidence": h.get("evidence_for", []) + h.get("evidence_against", []),
            "implication": h.get("implication", ""),
            "timestamp": datetime.now().isoformat(),
        })

    return {
        "hypotheses": updated,
        "log": log_entries,
    }