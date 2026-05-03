from langchain_community.chat_models import ChatOllama
from ..state import AnalysisState, LogEntry
from ..prompts import ITEM_ANALYSIS_PROMPT, SYSTEM_PROMPT, BRIEFING_FLAG_PROMPT, HYPOTHESIS_PROMPT
from datetime import datetime
import json
from ..config import llm

def briefing_analysis_node(state: AnalysisState) -> dict:
    """
    Iterates through briefing items one by one.
    Builds rolling context so later items can reference earlier findings.
    """
    items = state["briefing_items"]

    all_findings  = []
    all_log       = []
    all_queue     = []
    prior_context = []     # rolling window of prior findings
    queue_counter = 0

    for item in items:
        print("Briefing Item:", item)

        # Skip only explicitly low-confidence metrics with no signals
        if item.category == "metric":
            signals = item.data.get("signals", [])
            conf = (item.data.get("confidence", "") or "").upper()

            if not signals and conf == "LOW":
                print(f"Skipping low-confidence metric {item.id} {item.subject}", flush=True)
                continue

            print(f"Considering metric {item.id} {item.subject} (signals={signals}, confidence={conf})", flush=True)

        prompt = ITEM_ANALYSIS_PROMPT.format(
            ticker=state["ticker"],
            category=item.category,
            subject=item.subject,
            definition=item.definition or "N/A",
            data=json.dumps(item.data, indent=2),
            prior_context=json.dumps(prior_context[-8:], indent=2),  # last 8 findings
            item_id=item.id,
        )

        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ])
        result = parse_json(response.content)
        print("BRIEFING RAW RESPONSE:", getattr(response, "content", response), flush=True)
        print("BRIEFING PARSED RESULT:", result, flush=True)

        if not result:
            continue

        # Build finding
        finding = {
            "item_id":         item.id,
            "category":        item.category,
            "subject":         item.subject,
            "observation":     result.get("observation", ""),
            "implication":     result.get("implication", ""),
            "sentiment":       result.get("sentiment", "neutral"),
            "cross_references":result.get("cross_references", []),
            "confidence":      result.get("confidence", "LOW"),
            "needs_research":  result.get("needs_research", False),
        }
        all_findings.append(finding)

        # Log entry
        all_log.append({
            "node":      "briefing_analysis",
            "type":      "finding",
            "subject":   item.subject,
            "category":  item.category,
            "content":   result.get("observation", ""),
            "implication": result.get("implication", ""),
            "sentiment": result.get("sentiment", "neutral"),
            "confidence":result.get("confidence", "LOW"),
            "evidence":  [{"source": item.subject, "data": item.data}],
            "timestamp": datetime.now().isoformat(),
        })

        # Add to rolling context — compact summary only
        prior_context.append({
            "subject":    item.subject,
            "category":   item.category,
            "sentiment":  result.get("sentiment"),
            "implication":result.get("implication", "")[:120],
        })

        # Queue research items
        for ri in result.get("research_items", []):
            all_queue.append({
                "id":       f"rq_{queue_counter}",
                "type":     ri["type"],
                "priority": ri["priority"],
                "query":    ri["query"],
                "reason":   ri["reason"],
                "source":   item.subject,
                "status":   "pending",
                "attempts": 0,
            })
            queue_counter += 1

    return {
        "flagged_items":  all_findings,
        "research_queue": all_queue,
        "log":            all_log,
        "iteration":      0,
    }


def hypothesis_node(state: AnalysisState) -> dict:
    """Forms testable hypotheses from flagged unresolved findings."""

    print(f"Total flagged_items: {len(state['flagged_items'])}", flush=True)
    for f in state["flagged_items"]:
        print(f"  - {f['subject']}: needs_research={f.get('needs_research')}, confidence={f.get('confidence')}", flush=True)

    unresolved = [
        f for f in state["flagged_items"]
        if f.get("needs_research") and f.get("confidence") != "HIGH"
    ]

    print(f"Unresolved findings after filter: {len(unresolved)}", flush=True)

    if not unresolved:
        print("No unresolved findings — returning empty hypotheses", flush=True)
        return {"hypotheses": []}

    pending_queue = [
        q for q in state["research_queue"]
        if q["status"] == "pending"
    ]

    print(f"Pending queue items: {len(pending_queue)}", flush=True)

    prompt = HYPOTHESIS_PROMPT.format(
        findings=json.dumps(unresolved, indent=2),
        queue=json.dumps(pending_queue, indent=2)
    )

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt}
    ])

    result = parse_json(response.content)
    print("HYPOTHEIS RAW RESPONSE", response.content, flush=True)
    print("HYPOTHESE PARSED RESPONSE", result, flush=True)
    hypotheses = result.get("hypotheses", [])
    print(f"Hypotheses formed: {len(hypotheses)}", flush=True)

    # Copy queue so we can attach hypothesis_id to matching research items
    updated_queue = [dict(q) for q in state["research_queue"]]
    queue_by_id = {q.get("id"): q for q in updated_queue}

    log_entries = []
    for h in hypotheses:
        h.setdefault("evidence_for", [])
        h.setdefault("evidence_against", [])
        h.setdefault("status", "open")
        h.setdefault("confidence", 0.0)

        # Critical: link hypothesis to its queue items
        for qid in h.get("related_queue_ids", []):
            q = queue_by_id.get(qid)
            if q:
                q["hypothesis_id"] = h["id"]

        print("Hypothesis formed: ", h, flush=True)
        log_entries.append({
            "node":       "hypothesis_formation",
            "type":       "hypothesis",
            "subject":    h["id"],
            "content":    h["statement"],
            "explanation": f"Tests: {'; '.join(h['tests'])}",
            "confidence": 0.0,
            "evidence":   [],
            "timestamp":  datetime.now().isoformat(),
        })

    return {
        "hypotheses": hypotheses,
        "research_queue": updated_queue,   # return linked queue
        "log": log_entries,
    }


def parse_json(text: str) -> dict:
    import re
    try:
        clean = (text or "").strip()

        # If fenced code blocks exist, try each fenced section first
        if "```" in clean:
            parts = clean.split("```")
            for p in parts[1:]:
                p = p.strip()
                if p.lower().startswith("json"):
                    p = p[4:].strip()
                try:
                    return json.loads(p)
                except Exception:
                    continue

        # Search for JSON object or array anywhere in the text
        m = re.search(r"(\{.*\}|\[.*\])", clean, re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            return json.loads(candidate)

        # Fallback: attempt to load entire string
        return json.loads(clean)
    except Exception:
        return {}