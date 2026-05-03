from analysis.graph import build_graph
from analysis.ingest import get_chroma_client, ingest_filing_sections
import json

def run_analysis(
    ticker:   str,
    briefing: str,
    sections: dict,   # your parsed filing sections
    filings_metadata: list[dict],  # [{form, period}, ...]
):
    # 1. Ingest filing sections into vector DB first
    collection = get_chroma_client()
    for meta in filings_metadata:
        ingest_filing_sections(
            ticker=ticker,
            sections=sections,
            form=meta["form"],
            period=meta["period"],
            collection=collection
        )

    # 2. Build and run graph
    graph = build_graph()
    config = {"configurable": {"thread_id": f"{ticker}_analysis"}}

    result = graph.invoke(
        {
            "ticker":          ticker,
            "briefing":        briefing,
            "research_queue":  [],
            "hypotheses":      [],
            "log":             [],
            "flagged_items":   [],
            "retrieved_chunks":[],
            "web_results":     [],
            "hypothesis_results": [],
            "iteration":       0,
            "done":            False,
            "conclusion":      {},
        },
        config=config
    )

    return result


def print_report(result: dict):
    print("\n" + "="*60)
    print(f"ANALYSIS COMPLETE: {result['ticker']}")
    print("="*60)

    print(f"\nIterations: {result['iteration']}")
    print(f"Total log entries: {len(result['log'])}")

    print("\n--- HYPOTHESIS OUTCOMES ---")
    for h in result["hypotheses"]:
        print(f"  [{h.get('status','?').upper():12}] {h['statement'][:80]}")
        print(f"   Confidence: {h.get('confidence',0):.0%}")

    print("\n--- CONCLUSION ---")
    c = result["conclusion"]
    if c:
        print(f"  Trajectory:  {c.get('trajectory',{}).get('direction','?')}")
        print(f"  Confidence:  {c.get('overall_confidence',0):.0%}")
        print(f"\n  Risks:")
        for r in c.get("business_quality",{}).get("risks",[]):
            print(f"    • {r}")
        print(f"\n  Strengths:")
        for s in c.get("business_quality",{}).get("strengths",[]):
            print(f"    • {s}")

    print("\n--- FULL LOG ---")
    for entry in result["log"]:
        conf = entry.get("confidence", 0)
        conf_str = f"{float(conf):.0%}" if isinstance(conf, (int, float)) else str(conf)
        print(f"\n[{entry['node']:25}] [{entry['type']:10}] {conf_str}")
        print(f"  Subject: {entry['subject']}")
        print(f"  {entry['content'][:200]}")