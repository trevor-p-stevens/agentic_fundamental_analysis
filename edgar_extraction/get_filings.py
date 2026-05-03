import requests
from edgar_extraction.cik import HEADERS
from bs4 import BeautifulSoup
import re

SECTION_GENERAL_MAP = {
    "1": "Item 1",
    "1A": "Item 1A",
    "7": "Item 7",
    "8": "Item 8",
}


def get_filing_accessions_primary_docs(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = requests.get(url, headers=HEADERS).json()
    filings = data["filings"]["recent"]

    forms = filings["form"]
    accession_numbers = filings["accessionNumber"]
    filing_dates = filings["filingDate"]
    primary_doc = filings["primaryDocument"]

    ten_k_indices = [i for i, form in enumerate(forms) if form == "10-K"][:5]
    ten_q_indices = [i for i, form in enumerate(forms) if form == "10-Q"][:8]

    accession_numbers_10k = []
    accession_numbers_10q = []
    primary_doc_10k = []
    primary_doc_10q = []

    print("10-K accession numbers, dates, and primary docs:")
    for i in ten_k_indices:
        print(f"Accession: {accession_numbers[i]}, Date: {filing_dates[i]}, Primary Doc {primary_doc[i]}")
        accession_numbers_10k.append(accession_numbers[i])
        primary_doc_10k.append(primary_doc[i])

    print("\n10-Q accession numbers, dates, and primary docs:")
    for i in ten_q_indices:
        print(f"Accession: {accession_numbers[i]}, Date: {filing_dates[i]}, Primary Doc {primary_doc[i]}")
        accession_numbers_10q.append(accession_numbers[i])
        primary_doc_10q.append(primary_doc[i])

    return accession_numbers_10k, primary_doc_10k, accession_numbers_10q, primary_doc_10q

def normalize_section_key(key):
    # Remove non-breaking spaces and extra whitespace
    key = key.replace('\xa0', ' ')
    key = re.sub(r'\s+', ' ', key).strip()
    # Optionally, remove trailing page numbers or section numbers
    key = re.sub(r'\s*\|\s*.*$', '', key)
    return key

def clean_text(text):
    # Remove registered trademark, trademark, copyright, and similar symbols
    text = re.sub(r'[®©™℠]', '', text)
    # Remove common page footers/headers if needed (example for Apple Inc.)
    text = re.sub(r'Apple Inc\. \| [\d]{4} Form 10-K \| \d+', '', text)
    # Remove extra spaces left after symbol removal
    text = re.sub(r' +', ' ', text)
    return text

def generalize_section_key(key):
    # Match "Item 1", "Item 1A", "Item 7", "Item 8" at the start, with optional punctuation/words after
    m = re.match(r"Item\s*(1A|1|7|8)\b", key, re.IGNORECASE)
    if m:
        return f"Item {m.group(1).upper()}"
    return None  # Ignore sections that don't match

def parse_filing(html: str, form_type="10-K") -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(re.compile(r'^ix:')):
        tag.unwrap()

    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            rows.append(" | ".join(cells))
        table.replace_with("\n" + "\n".join(rows) + "\n")

    raw = soup.get_text(separator="\n", strip=True)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    raw = clean_text(raw)

    pattern = r'(?=^Item\s+\d+[A-Za-z]?[\s\.\-—])'
    parts = re.split(pattern, raw, flags=re.MULTILINE | re.IGNORECASE)

    sections = {}
    for part in parts:
        if not part.strip():
            continue
        first_line = part.split('\n')[0].strip()
        norm_key = normalize_section_key(first_line)
        gen_key = generalize_section_key(norm_key)
        if gen_key:
            if gen_key not in sections:
                sections[gen_key] = part.strip()
            else:
                # Concatenate if multiple parts for the same section
                sections[gen_key] += "\n\n" + part.strip()

    # Optionally filter out very short sections
    sections = {k: v for k, v in sections.items() if len(v) > 300}
    return sections

def get_filing_html_text(cik, accession, primary_doc, form_type):
    accession_clean = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{primary_doc}"
    res = requests.get(url, headers=HEADERS)
    html = res.text
    return parse_filing(html, form_type)  # returns dict[str, str] of high-signal sections


# accession_numbers_10k, primary_doc_10k, accession_numbers_10q, primary_doc_10q = get_filing_accessions_primary_docs('0000320193')
# sections = get_filing_html_text('0000320193', accession_numbers_10k[0], primary_doc_10k[0], "10-K")
# print(sections.keys())
# with open("parsed_filing_10k.txt", "w", encoding="utf-8") as f:
#     for section, text in sections.items():
#         f.write(f"=== {section} ===\n{text}\n\n")

# sections = get_filing_html_text('0000320193', accession_numbers_10q[0], primary_doc_10q[0], "10-Q")
# print(sections.keys())
# with open("parsed_filing_10q.txt", "w", encoding="utf-8") as f:
#     for section, text in sections.items():
#         f.write(f"=== {section} ===\n{text}\n\n")