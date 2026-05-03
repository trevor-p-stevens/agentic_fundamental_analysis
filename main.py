import json

from analysis.graph import build_graph
from analysis.ingest import get_chroma_client, ingest_filing_sections
from edgar_extraction.cik import get_cik
from edgar_extraction.get_filings import (
    get_filing_accessions_primary_docs,
    get_filing_html_text,
)
from edgar_extraction.xbrl import get_us_gaap, get_xbrl
from metrics.evaluate_metrics import (
    basic_forecast,
    build_dataframe,
    business_quality_score,
    eval_metrics,
)
from metrics.metric import build_master_metrics
from metrics.metrics_json import canonical_metrics_json
from translation_layer.llm_briefing import (
    build_anomaly_brief,
    build_llm_briefing,
    briefing_to_items,
    prioritize_metrics,
)

def clear_collection():
    """Clear all documents from the Chroma collection."""
    from analysis.ingest import get_chroma_client
    collection = get_chroma_client()
    # Get all IDs in the collection
    all_docs = collection.get()
    if all_docs["ids"]:
        collection.delete(ids=all_docs["ids"])
        print(f"Cleared {len(all_docs['ids'])} documents from collection.")

def build_report(result: dict) -> str:
    """Extract and format the comprehensive report from synthesis."""
    for entry in result.get("log", []):
        if entry.get("node") == "synthesis" and entry.get("type") == "judgment":
            return entry.get("content", "No report generated.")
    return "Analysis complete but no report found."

def main():
    ticker = input("Enter ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    cik = get_cik(ticker)
    print("CIK:", cik)

    accession_numbers_10k, primary_doc_10k, accession_numbers_10q, primary_doc_10q = (
        get_filing_accessions_primary_docs(cik)
    )

    xbrl_data = get_xbrl(cik)
    us_gaaps_10k = [get_us_gaap(xbrl_data, acc) for acc in accession_numbers_10k]
    us_gaaps_10q = [get_us_gaap(xbrl_data, acc) for acc in accession_numbers_10q]

    metrics_10k, metrics_10q = build_master_metrics(
        us_gaaps_10k,
        us_gaaps_10q,
        cik,
        accession_numbers_10k,
        accession_numbers_10q,
        primary_doc_10k,
        primary_doc_10q,
    )

    with open("metrics_10k.json", "w") as f:
        json.dump(metrics_10k, f, indent=2)

    with open("metrics_10q.json", "w") as f:
        json.dump(metrics_10q, f, indent=2)

    df_annual = build_dataframe(metrics_10k)
    df_quarterly = build_dataframe(metrics_10q)

    df_annual.to_csv("annual_metrics.csv", index=True)
    df_quarterly.to_csv("quarterly_metrics.csv", index=True)

    all_metrics_annual = eval_metrics(df_annual, "annual", ticker=ticker)
    all_metrics_annual.to_csv("all_metrics_annual.csv", index=True)

    all_metrics_quarterly = eval_metrics(df_quarterly, "quarterly", ticker=ticker)
    all_metrics_quarterly.to_csv("all_metrics_quarterly.csv", index=True)

    score, score_log = business_quality_score(all_metrics_annual)
    with open("business_quality_score_log.txt", "w") as f:
        for line in score_log:
            f.write(line + "\n")
        f.write(f"Total Score: {score}/4\n")

    forecast_df = basic_forecast(all_metrics_annual, years_ahead=3)
    print(forecast_df)
    forecast_df.to_csv("forecast_scenarios.csv", index=False)

    final_json = canonical_metrics_json(all_metrics_annual)
    with open("final_json.json", "w") as f:
        json.dump(final_json, f, indent=2)

    with open("final_json.json") as f:
        data = json.load(f)

    grouped = prioritize_metrics(data["metrics"], data.get("anomalies", []))
    anomalies = build_anomaly_brief(data["anomalies"])
    briefing = build_llm_briefing(
        grouped,
        anomalies,
        ticker=ticker,
        all_metrics=data["metrics"],
        advanced_signals=data.get("advanced_signals", []),
    )

    with open("final_breifing.txt", "w") as f:
        f.write(briefing)

    # Build structured briefing items for the analysis graph
    briefing_items = briefing_to_items(
        grouped,
        anomalies,
        ticker=ticker,
        all_metrics=data["metrics"],
        advanced_signals=data.get("advanced_signals", []),
    )

    print("briefing_items:", len(briefing_items))
    print("sample briefing item:", briefing_items[0] if briefing_items else "NONE")

    # Ingest latest filing sections for retrieval
    collection = get_chroma_client()
    if accession_numbers_10k and primary_doc_10k:
        sections_10k = get_filing_html_text(cik, accession_numbers_10k[0], primary_doc_10k[0], "10-K")
        ingest_filing_sections(
            ticker=ticker,
            sections=sections_10k,
            form="10-K",
            period=accession_numbers_10k[0],
            collection=collection,
        )

    if accession_numbers_10q and primary_doc_10q:
        sections_10q = get_filing_html_text(cik, accession_numbers_10q[0], primary_doc_10q[0], "10-Q")
        ingest_filing_sections(
            ticker=ticker,
            sections=sections_10q,
            form="10-Q",
            period=accession_numbers_10q[0],
            collection=collection,
        )

    # Run graph analysis
    graph = build_graph()
    config = {"configurable": {"thread_id": f"{ticker}_analysis"}}
    result = graph.invoke(
        {
            "ticker": ticker,
            "briefing_items": briefing_items,
            "research_queue": [],
            "hypotheses": [],
            "iteration": 0,
            "seen_urls": [],
            "log": [],
            "flagged_items": [],
            "retrieved_chunks": [],
            "web_results": [],
            "hypothesis_results": [],
            "conclusion": {},
            "done": False,
        },
        config=config,
    )

    report_text = build_report(result)
    print(report_text)

    out_file = f"{ticker}_analysis.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nSaved comprehensive analysis report to {out_file}")

    clear_collection()


if __name__ == "__main__":
    main()