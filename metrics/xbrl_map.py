import json
import os
from weasyprint import HTML
import requests
from edgar_extraction.cik import HEADERS

XBRL_MAP_PATH = "./metrics/xbrl_map.json"
MISSING_PATH = "missing_xbrl_labels.json"

def load_xbrl_map():
    if os.path.exists(XBRL_MAP_PATH):
        with open(XBRL_MAP_PATH, "r") as f:
            return json.load(f)
    return {}

def save_xbrl_map(xbrl_map):
    with open(XBRL_MAP_PATH, "w") as f:
        json.dump(xbrl_map, f, indent=2)

def save_missing(metric, us_gaap_data):
    # Save all available tags/labels for user inspection
    available = sorted(set(
        e.get("tag") or e.get("label")
        for e in us_gaap_data if e.get("tag") or e.get("label")
    ))
    with open(MISSING_PATH, "w") as f:
        json.dump({metric: available}, f, indent=2)

def fetch_and_save_pdf(cik, accession, primary_doc, save_path):
    accession_clean = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{primary_doc}"
    html = requests.get(url, headers=HEADERS).text
    HTML(string=html).write_pdf('output.pdf') # or use weasyprint
    print(f"Saved filing as PDF: {save_path}")

def get_metric_value(us_gaap_data, metric, cik=None, accession=None, primary_doc=None):
    xbrl_map = load_xbrl_map()
    labels = xbrl_map.get(metric, [])
    if isinstance(labels, str):
        labels = [labels]
    matches = []
    for label in labels:
        for entry in us_gaap_data:
            if entry.get("tag") == label or entry.get("label") == label:
                period_end = entry.get("end")
                value = entry.get("value")
                matches.append({"period_end": period_end, "value": value})
    if matches:
        return matches
    # If none work, prompt user as before
    save_missing(metric, us_gaap_data)
    print(f"\nMetric '{metric}' not found with current mapping.")
    print(f"All available tags/labels have been saved to {MISSING_PATH}.")
    print("Please open that file, search for the correct tag/label, and enter it below.")
    while True:
        user_input = input(
            f"Enter the tag or label to use for '{metric}' "
            "(or type 'missing' to fetch filing, or 'none' if not present): "
        ).strip()
        if user_input.lower() == "none":
            print(f"No value for '{metric}' will be recorded.")
            return []
        if user_input.lower() == "missing":
            if cik and accession and primary_doc:
                pdf_path = f"{metric}_{accession}.pdf"
                fetch_and_save_pdf(cik, accession, primary_doc, pdf_path)
                print("Please open the PDF and enter period_end,value pairs (e.g. 2023-09-30,123456). Type 'next' when done.")
                manual_entries = []
                while True:
                    pair = input("period_end,value (or 'next'): ").strip()
                    if pair.lower() == "next":
                        break
                    if pair.lower() == "none":
                        print(f"No value for '{metric}' will be recorded.")
                        return []
                    try:
                        period_end, value = pair.split(",")
                        manual_entries.append({"period_end": period_end.strip(), "value": float(value.strip())})
                    except Exception:
                        print("Invalid input. Please enter as period_end,value")
                return manual_entries
            else:
                print("Missing filing context (cik, accession, primary_doc). Cannot fetch filing.")
                continue
        for entry in us_gaap_data:
            if entry.get("tag") == user_input or entry.get("label") == user_input:
                period_end = entry.get("end")
                value = entry.get("value")
                labels.append(user_input)
                xbrl_map[metric] = labels
                save_xbrl_map(xbrl_map)
                return [{"period_end": period_end, "value": value}]
        print(f"Label '{user_input}' not found in data. Please try again.")

