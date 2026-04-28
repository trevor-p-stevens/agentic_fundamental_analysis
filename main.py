import json

from edgar_extraction.cik import get_cik
from edgar_extraction.get_filings import get_filing_accessions_primary_docs, get_filing_html_text
from edgar_extraction.xbrl import get_us_gaap, get_xbrl
from metrics.metric import build_master_metrics
from metrics.xbrl_map import get_metric_value


cik = get_cik("AAPL")
print("CIK:", cik)

accession_numbers_10k, primary_doc_10k, accession_numbers_10q, primary_doc_10q = get_filing_accessions_primary_docs('0000320193')
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
xbrl_data = get_xbrl(cik)
us_gaaps_10k = [get_us_gaap(xbrl_data, accession_numbers_10k[i]) for i in range(len(accession_numbers_10k))]
us_gaaps_10q = [get_us_gaap(xbrl_data, accession_numbers_10q[i]) for i in range(len(accession_numbers_10q))]

metrics_10k, metrics_10q = build_master_metrics(us_gaaps_10k, us_gaaps_10q, cik, accession_numbers_10k, accession_numbers_10q, primary_doc_10k, primary_doc_10q)

with open("metrics_10k.json", 'w') as f:
    json.dump(metrics_10k, f, indent=2)


