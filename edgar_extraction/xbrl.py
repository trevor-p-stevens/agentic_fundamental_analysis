from edgar_extraction.cik import HEADERS
import requests

def get_xbrl(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    data = requests.get(url, headers=HEADERS).json()
    return data

def normalize_val(val, decimals):
    if decimals is None or decimals == "INF":
        return val
    try:
        return val * (10 ** int(decimals))
    except Exception:
        return val

def get_dei(data, accession):
    dei_facts = data.get("facts", {}).get("dei", {})
    results = []
    for tag, fact in dei_facts.items():
        units = fact.get("units", {})
        for unit, items in units.items():
            for item in items:
                if item.get("accn") == accession:
                    val = item.get("val")
                    decimals = item.get("decimals")
                    norm_val = normalize_val(val, decimals)
                    entry = {
                        "label": fact.get("label"),
                        "value": norm_val,
                        "unit": unit,
                        "decimals": decimals
                    }
                    # Add important differentiators if present
                    for key in ["end", "start", "frame", "fy", "fp", "form", "contextRef"]:
                        if key in item:
                            entry[key] = item[key]
                    results.append(entry)
    return results

def get_us_gaap(data, accession):
    us_gaap_facts = data.get("facts", {}).get("us-gaap", {})
    results = []
    for tag, fact in us_gaap_facts.items():
        units = fact.get("units", {})
        for unit, items in units.items():
            for item in items:
                if item.get("accn") == accession:
                    val = item.get("val")
                    decimals = item.get("decimals")
                    norm_val = normalize_val(val, decimals)
                    entry = {
                        "label": fact.get("label"),
                        "value": norm_val,
                        "unit": unit,
                        "decimals": decimals
                    }
                    # Add important differentiators if present
                    for key in ["end", "start", "frame", "fy", "fp", "form", "contextRef"]:
                        if key in item:
                            entry[key] = item[key]
                    results.append(entry)
    return results