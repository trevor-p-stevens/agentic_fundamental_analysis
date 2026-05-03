from analysis.nodes.briefing import parse_json
from ..config import llm
from ..state import AnalysisState
from ..prompts import SYSTEM_PROMPT
from datetime import datetime
import json

def _format_research_log(log: dict) -> str:
    lines = []
    question = log.get("question") or log.get("subject")
    if question:
        lines.append(f"Question: {question}")

    answer = log.get("answer")
    if answer:
        lines.append(f"Answer: {answer}")

    finding = log.get("finding") or log.get("content")
    if finding:
        lines.append(f"Finding: {finding}")

    implication = log.get("implication")
    if implication:
        lines.append(f"Why it matters: {implication}")

    hypothesis_update = log.get("hypothesis_update")
    if hypothesis_update:
        lines.append(f"Hypothesis update: {hypothesis_update}")

    if log.get("sources_checked") is not None:
        lines.append(f"Sources checked: {log.get('sources_checked')}")

    if log.get("evidence") is not None:
        lines.append(f"Evidence citations: {len(log.get('evidence', []))}")

    return "\n".join(lines)

def build_comprehensive_report(state: AnalysisState, ticker: str) -> str:
    """
    Build a long-form narrative report that walks through:
    1. Briefing findings grouped by theme
    2. Text research results
    3. Web research results
    4. Hypothesis testing outcomes
    """
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append(f"COMPREHENSIVE FINANCIAL ANALYSIS: {ticker}")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ========== SECTION 1: BRIEFING ANALYSIS OVERVIEW ==========
    lines.append("\n" + "─" * 80)
    lines.append("SECTION 1: BRIEFING ANALYSIS OVERVIEW")
    lines.append("─" * 80)
    
    briefing_logs = [l for l in state["log"] if l["node"] == "briefing_analysis"]
    lines.append(f"\nTotal briefing items analyzed: {len(briefing_logs)}")
    lines.append("\nKey findings from financial metrics and signals:")
    
    # Group findings by sentiment/category
    high_conf = [l for l in briefing_logs if l.get("confidence") == "HIGH"]
    medium_conf = [l for l in briefing_logs if l.get("confidence") == "MEDIUM"]
    low_conf = [l for l in briefing_logs if l.get("confidence") == "LOW"]
    
    if high_conf:
        lines.append(f"\n  Positive/Strong indicators ({len(high_conf)}):")
        for log in high_conf[:10]:
            lines.append(f"    • {log['subject']}: {log['content']}")
    
    if medium_conf:
        lines.append(f"\n  Mixed/Moderate indicators ({len(medium_conf)}):")
        for log in medium_conf[:10]:
            lines.append(f"    • {log['subject']}: {log['content']}")
    
    if low_conf:
        lines.append(f"\n  Concerns/Weak indicators ({len(low_conf)}):")
        for log in low_conf[:5]:
            lines.append(f"    • {log['subject']}: {log['content']}")

    # ========== SECTION 2: TEXT RESEARCH FINDINGS ==========
    text_logs = [l for l in state["log"] if l["node"] == "text_research"]
    if text_logs:
        lines.append(f"\nFiling analyses performed: {len(text_logs)}")
        for log in text_logs:
            lines.append("")
            lines.extend(_format_research_log(log).split("\n"))
    else:
        lines.append("\n  No filing text analysis performed.")

    # ========== SECTION 3: WEB RESEARCH FINDINGS ==========
    web_logs = [l for l in state["log"] if l["node"] == "web_research"]
    if web_logs:
        lines.append(f"\nWeb research queries completed: {len(web_logs)}")
        for log in web_logs:
            lines.append("")
            lines.extend(_format_research_log(log).split("\n"))
    else:
        lines.append("\n  No web research performed.")

    # ========== SECTION 4: HYPOTHESIS TESTING ==========
    lines.append("\n\n" + "─" * 80)
    lines.append("SECTION 4: HYPOTHESIS TESTING & CONCLUSIONS")
    lines.append("─" * 80)
    
    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        lines.append(f"\nHypotheses formed and tested: {len(hypotheses)}")
        
        for h in hypotheses:
            lines.append(f"\n  Hypothesis: {h.get('statement', 'N/A')}")
            lines.append(f"  Status: {h.get('status', '?').upper()}")
            
            if h.get("evidence_for"):
                lines.append(f"  Evidence supporting: {len(h['evidence_for'])} items")
                for e in h['evidence_for'][:2]:
                    if isinstance(e, dict):
                        lines.append(f"    ✓ {str(e)}")
            
            if h.get("evidence_against"):
                lines.append(f"  Evidence against: {len(h['evidence_against'])} items")
                for e in h['evidence_against'][:2]:
                    if isinstance(e, dict):
                        lines.append(f"    ✗ {str(e)}")
            
            if h.get("conclusion"):
                lines.append(f"  Conclusion: {h.get('conclusion', '')}")
    else:
        lines.append("\n  No testable hypotheses formed.")
    
    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def synthesis_node(state: AnalysisState) -> dict:
    """
    Final synthesis: iterate over each section and generate conclusions,
    then provide a final overall assessment.
    """
    print("Building comprehensive analysis report...")
    
    ticker = state.get("ticker", "UNKNOWN")
    full_report = build_comprehensive_report(state, ticker)
    
    # Extract logs by section
    briefing_logs = [l for l in state["log"] if l["node"] == "briefing_analysis"]
    text_logs = [l for l in state["log"] if l["node"] == "text_research"]
    web_logs = [l for l in state["log"] if l["node"] == "web_research"]
    eval_logs = [l for l in state["log"] if l["node"] == "hypothesis_evaluation"]
    
    section_conclusions = {}
    
    # Section 1: Briefing Analysis Conclusion
    print("  Generating Briefing Analysis conclusion...")
    if briefing_logs:
        prompt = f"""Based on these briefing analysis findings for {ticker}:

{json.dumps(briefing_logs[-15:], indent=2)}

Provide a 2-3 sentence conclusive summary of what the financial metrics and signals reveal. Focus on patterns and trends, not scores. Return plain text only, no JSON."""
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        section_conclusions["Briefing Analysis"] = response.content
    
    # Section 2: Text Research Conclusion
    print("  Generating Text Research conclusion...")
    if text_logs:
        prompt = f"""Based on these filing text research findings for {ticker}:

{json.dumps(text_logs, indent=2)}

Provide a 2-3 sentence conclusive summary of what the filing analysis revealed about the company's financials. Return plain text only, no JSON."""
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        section_conclusions["Text Research"] = response.content
    
    # Section 3: Web Research Conclusion
    print("  Generating Web Research conclusion...")
    if web_logs:
        prompt = f"""Based on these external research findings for {ticker}:

{json.dumps(web_logs[:8], indent=2)}

Provide a 2-3 sentence conclusive summary of what external sources and context revealed. Return plain text only, no JSON."""
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        section_conclusions["Web Research"] = response.content
    
    # Section 4: Hypothesis Testing Conclusion
    print("  Generating Hypothesis Testing conclusion...")
    if eval_logs:
        prompt = f"""Based on these hypothesis evaluation results for {ticker}:

{json.dumps(eval_logs, indent=2)}

Provide a 2-3 sentence conclusive summary of what the hypothesis testing revealed. Return plain text only, no JSON."""
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        section_conclusions["Hypothesis Testing"] = response.content
    
    # Final Overall Conclusion
    print("  Generating Final Overall Assessment...")
    all_conclusions_text = "\n\n".join([f"**{k}:**\n{v}" for k, v in section_conclusions.items()])
    
    final_prompt = f"""You have analyzed {ticker} across four research sections:

{all_conclusions_text}

Provide a final 2-3 paragraph assessment of {ticker}'s overall financial health, business trajectory, and key takeaways based on all sections. Return plain text only, no JSON."""
    
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": final_prompt}
    ])
    final_conclusion = response.content
    
    # Build final summary section
    summary_section = "\n\n" + "=" * 80
    summary_section += "\nSECTION CONCLUSIONS"
    summary_section += "\n" + "=" * 80
    
    for section_name, conclusion in section_conclusions.items():
        summary_section += f"\n\n{section_name.upper()}\n"
        summary_section += f"{conclusion}\n"
    
    summary_section += "\n\n" + "=" * 80
    summary_section += "\nFINAL OVERALL ASSESSMENT"
    summary_section += "\n" + "=" * 80
    summary_section += f"\n\n{final_conclusion}"
    
    full_report += summary_section
    
    log_entry = {
        "node":       "synthesis",
        "type":       "judgment",
        "subject":    "FINAL COMPREHENSIVE REPORT",
        "content":    full_report,
        "confidence": 0,
        "evidence":   [],
        "timestamp":  datetime.now().isoformat(),
    }

    return {
        "conclusion": {},
        "log":        [log_entry],
        "done":       True,
    }