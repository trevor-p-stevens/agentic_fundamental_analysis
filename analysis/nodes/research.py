from analysis.nodes.briefing import parse_json
from ..state import AnalysisState
from ..prompts import SYSTEM_PROMPT, WEB_CHUNK_PROMPT, TEXT_RESEARCH_PROMPT
from ..ingest import EARLY_STOP_CONFIDENCE, MAX_URLS_PER_ITEM, hybrid_search, infer_sections, get_chroma_client, ingest_and_retrieve, rank_url
from datetime import datetime
import hashlib
import json
from ..config import llm
import requests

collection = get_chroma_client()

ORIOSEARCH_URL = "http://localhost:8000/search"

def tavily_search(query: str, search_depth: str = "advanced", max_results: int = 5, include_raw_content: bool = True):
    resp = requests.post(
        ORIOSEARCH_URL,
        json={
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

def _summarize_source_finding(summary: dict, index: int) -> str:
    lines = [f"Source {index}:"]
    if summary.get("answer"):
        lines.append(f"Answer: {summary['answer']}")
    if summary.get("finding"):
        lines.append(f"Finding: {summary['finding']}")
    if summary.get("implication"):
        lines.append(f"Why it matters: {summary['implication']}")
    return "\n".join(lines)


WEB_QUERY_TEMPLATES = {
    "earnings_transcript": "{ticker} earnings call transcript {year}",
    "investor_presentation": "{ticker} investor day presentation",
    "industry":              "{ticker} industry analysis market size",
    "competitor":            "{ticker} competitors market share comparison",
    "management":            "{ticker} CEO CFO background track record",
    "regulation":            "{ticker} regulatory risk antitrust",
    "product":               "{ticker} product revenue breakdown segment",
    "guidance":              "{ticker} revenue guidance outlook analyst",
}

SOURCE_TYPE_MAP = {
    "sec.gov":             "sec_filing",
    "earnings":            "earnings_transcript",
    "investor":            "investor_presentation",
    "bloomberg.com":       "news",
    "reuters.com":         "news",
    "wsj.com":             "news",
    "seekingalpha.com":    "news",
}

def classify_url(url: str) -> str:
    url_lower = url.lower()
    for domain, stype in SOURCE_TYPE_MAP.items():
        if domain in url_lower:
            return stype
    return "news"


def web_research_node(state: AnalysisState) -> dict:
    """Process web research and aggregate findings per query."""
    web_items = sorted(
        [q for q in state["research_queue"]
         if q["type"] == "web" and q["status"] == "pending"],
        key=lambda x: x["priority"]
    )[:3]

    if not web_items:
        return {
            "web_results": [],
            "log":         [],
            "research_queue": state["research_queue"],
            "hypotheses": state["hypotheses"],
            "seen_urls": state.get("seen_urls", [])
        }

    seen_urls          = set(state.get("seen_urls", []))
    new_seen_urls      = []
    log_entries        = []
    all_results        = []
    new_queue_items    = []
    updated_hypotheses = list(state["hypotheses"])

    for item in web_items:
        item["status"]   = "in_progress"
        item["attempts"] += 1
        item_findings    = []  # Collect findings for this query

        print("Web researching: ", item)
        try:
            search_response = tavily_search(
                query=item["query"],
                search_depth="advanced",
                max_results=MAX_URLS_PER_ITEM,
                include_raw_content=True,
            )
            candidates = search_response.get("results", [])
        except Exception as e:
            item["status"] = "abandoned"
            log_entries.append(_error_log("web_research", item["query"], str(e)))
            continue

        new_candidates = [
            r for r in candidates
            if r.get("url") and r["url"] not in seen_urls
        ]

        if not new_candidates:
            log_entries.append({
                "node":      "web_research",
                "type":      "research",
                "subject":   item["query"],
                "content":   "No new sources found",
                "confidence": 0,
                "evidence":  [],
                "timestamp": datetime.now().isoformat(),
            })
            item["status"] = "done"
            continue

        new_candidates.sort(key=lambda r: rank_url(r.get("url", "")), reverse=True)

        hyp = next(
            (h for h in updated_hypotheses
             if item.get("hypothesis_id") == h.get("id")),
            None
        )
        hypothesis_context = hyp["statement"] if hyp else item["reason"]

        item_best_confidence = 0.0
        source_summaries = []  # Collect findings from each source

        for candidate in new_candidates:
            url     = candidate.get("url", "")
            content = candidate.get("raw_content", "") or candidate.get("content", "")

            if not content or len(content) < 200:
                seen_urls.add(url)
                new_seen_urls.append(url)
                continue

            seen_urls.add(url)
            new_seen_urls.append(url)

            try:
                relevant_chunks = ingest_and_retrieve(
                    url=url,
                    content=content,
                    ticker=state["ticker"],
                    query=item["query"],
                )
            except Exception as e:
                log_entries.append(_error_log("web_research", url, str(e)))
                continue

            if not relevant_chunks:
                continue

            prompt = WEB_CHUNK_PROMPT.format(
                ticker=state["ticker"],
                question=item["reason"],
                hypothesis=hypothesis_context,
                source_url=url,
                source_rank=rank_url(url),
                chunks=_format_chunks(relevant_chunks),
            )

            response = llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ])
            result = parse_json(response.content)

            if not result:
                continue

            confidence = float(result.get("confidence", 0))
            item_best_confidence = max(item_best_confidence, confidence)

            # Collect source findings for aggregation
            source_summaries.append({
                "url": url,
                "answer": result.get("answer", ""),
                "finding": result.get("finding", ""),
                "implication": result.get("implication", ""),
                "confidence": confidence,
            })

            # Update hypothesis evidence
            if hyp and confidence > 0.4:
                update = result.get("hypothesis_update", "")
                if update == "confirms":
                    hyp["evidence_for"].extend(result.get("evidence", []))
                elif update == "rejects":
                    hyp["evidence_against"].extend(result.get("evidence", []))

            all_results.append({
                "query": item["query"],
                "url": url,
                "answer": result.get("answer", ""),
                "finding": result.get("finding", ""),
                "implication": result.get("implication", ""),
                "confidence": confidence,
            })

            if item_best_confidence >= EARLY_STOP_CONFIDENCE:
                break

        # Log ONE aggregated finding per query across all sources
        aggregate_parts = [
            _summarize_source_finding(s, i + 1)
            for i, s in enumerate(source_summaries[:2])
        ]
        aggregate_finding = "\n\n".join(aggregate_parts) if aggregate_parts else "No findings from web sources"

        log_entries.append({
            "node": "web_research",
            "type": "research",
            "subject": item["query"],
            "question": item["query"],
            "hypothesis_id": item.get("hypothesis_id", ""),
            "answer": source_summaries[0]["answer"] if source_summaries else "",
            "content": aggregate_finding,
            "finding": source_summaries[0]["finding"] if source_summaries else "",
            "implication": source_summaries[0]["implication"] if source_summaries else "",
            "sources_checked": len(source_summaries),
            "confidence": item_best_confidence,
            "evidence": source_summaries[:2],
            "timestamp": datetime.now().isoformat(),
        })

        # Queue follow-ups if confidence low
        if item_best_confidence < 0.4 and len(source_summaries) > 0:
            new_queue_items.append({
                "id":            f"web_fu_{len(state['research_queue']) + len(new_queue_items)}",
                "type":          "web",
                "priority":      max(item["priority"] + 1, 4),
                "query":         f"{item['query']} {state['ticker']} detailed analysis",
                "reason":        f"Low confidence follow-up: {item['reason']}",
                "source":        item["source"],
                "status":        "pending",
                "attempts":      0,
                "hypothesis_id": item.get("hypothesis_id", ""),
            })

        item["status"] = "done"

    return {
        "web_results":    all_results,
        "seen_urls":      list(seen_urls) + new_seen_urls,
        "research_queue": state["research_queue"] + new_queue_items,
        "hypotheses":     updated_hypotheses,
        "log":            log_entries,
    }


def text_research_node(state: AnalysisState) -> dict:
    """Process text research items and aggregate findings per query."""
    text_items = sorted(
        [q for q in state["research_queue"]
         if q["type"] == "text" and q["status"] == "pending"],
        key=lambda x: x["priority"]
    )[:5]

    if not text_items:
        return {"retrieved_chunks": [], "log": [], "research_queue": state["research_queue"], "hypotheses": state["hypotheses"]}

    log_entries        = []
    all_chunks         = []
    new_queue_items    = []
    updated_hypotheses = list(state["hypotheses"])

    for item in text_items:
        print("Text Researching: ", item)
        sections = infer_sections(item["query"])
        chunks   = hybrid_search(
            query=item["query"],
            ticker=state["ticker"],
            collection=collection,
            section_filter=sections,
            k=6,
        )

        if not chunks:
            item["status"] = "abandoned"
            log_entries.append({
                "node":      "text_research",
                "type":      "research",
                "subject":   item["query"],
                "content":   "No relevant filing text found",
                "confidence": 0,
                "evidence":  [],
                "timestamp": datetime.now().isoformat(),
            })
            continue

        hyp = next(
            (h for h in updated_hypotheses
             if item.get("hypothesis_id") == h.get("id")),
            None
        )

        prompt = TEXT_RESEARCH_PROMPT.format(
            ticker=state["ticker"],
            question=hyp["statement"] if hyp else item["reason"],
            reason=item["reason"],
            chunks=_format_chunks(chunks),
        )

        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ])
        result = parse_json(response.content)

        confidence = float(result.get("confidence", 0))

        answer = result.get("answer", "")
        finding = result.get("finding", answer or "No finding extracted")
        implication = result.get("implication", "")

        if hyp:
            update = result.get("hypothesis_update", "")
            if update == "confirms":
                hyp["evidence_for"].extend(result.get("evidence", []))
            elif update == "rejects":
                hyp["evidence_against"].extend(result.get("evidence", []))

        log_entries.append({
            "node": "text_research",
            "type": "research",
            "subject": item["query"],
            "question": item["query"],
            "hypothesis_id": item.get("hypothesis_id", ""),
            "answer": answer,
            "content": finding,
            "finding": finding,
            "implication": implication,
            "addresses": result.get("addresses", "NO"),
            "hypothesis_update": result.get("hypothesis_update", "inconclusive"),
            "confidence": confidence,
            "evidence_count": len(result.get("evidence", [])),
            "evidence": result.get("evidence", [])[:3],
            "timestamp": datetime.now().isoformat(),
        })

        # Escalate to web if text is insufficient
        for wq in result.get("new_web_queries", []):
            new_queue_items.append({
                "id":            f"web_{len(state['research_queue']) + len(new_queue_items)}",
                "type":          "web",
                "priority":      2,
                "query":         wq,
                "reason":        f"Text insufficient — escalating: {item['reason']}",
                "source":        item["source"],
                "status":        "pending",
                "attempts":      0,
                "hypothesis_id": item.get("hypothesis_id", ""),
            })

        item["status"] = "done"
        all_chunks.extend(chunks)

    return {
        "retrieved_chunks": all_chunks,
        "research_queue":   state["research_queue"] + new_queue_items,
        "hypotheses":       updated_hypotheses,
        "log":              log_entries,
    }

def format_chunks(chunks: list[dict]) -> str:
    lines = []
    for c in chunks:
        meta = c["metadata"]
        lines.append(
            f"[{meta.get('section','Unknown')} | "
            f"{meta.get('form','?')} {meta.get('period','?')} | "
            f"score: {c['score']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(lines)

def _format_chunks(chunks: list[dict]) -> str:
    lines = []
    for c in chunks:
        meta = c.get("metadata", {})
        src  = meta.get("url") or meta.get("section") or "unknown"
        lines.append(
            f"[Source: {src} | Score: {c.get('score', 0):.2f}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(lines)


def _error_log(node: str, subject: str, error: str) -> dict:
    return {
        "node":      node,
        "type":      "finding",
        "subject":   subject,
        "content":   f"Error: {error}",
        "confidence": 0,
        "evidence":  [],
        "timestamp": datetime.now().isoformat(),
    }