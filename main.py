import json

from edgar_extraction.cik import get_cik
from edgar_extraction.get_filings import get_filing_accessions_primary_docs, get_filing_html_text
from edgar_extraction.xbrl import get_us_gaap, get_xbrl
from metrics.evaluate_metrics import basic_forecast, build_dataframe, business_quality_score, eval_metrics
from metrics.metric import build_master_metrics
from metrics.metrics_json import canonical_metrics_json
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

with open("metrics_10q.json", 'w') as f:
    json.dump(metrics_10q, f, indent=2)

df_annual    = build_dataframe(metrics_10k)
df_quarterly = build_dataframe(metrics_10q)

df_annual.to_csv("annual_metrics.csv", index=True)
df_quarterly.to_csv("quarterly_metrics.csv", index=True)

all_metrics_annual = eval_metrics(df_annual, "annual", ticker="AAPL")
all_metrics_annual.to_csv("all_metrics_annual.csv", index=True)

all_metrics_quarterly = eval_metrics(df_quarterly, "quarterly", ticker="AAPL")
all_metrics_quarterly.to_csv("all_metrics_quarterly.csv", index=True)

score, log = business_quality_score(all_metrics_annual)
# Optionally, save log to a file
with open("business_quality_score_log.txt", "w") as f:
    for line in log:
        f.write(line + "\n")
    f.write(f"Total Score: {score}/4\n")

forecast_df = basic_forecast(all_metrics_annual, years_ahead=3)
print(forecast_df)
forecast_df.to_csv("forecast_scenarios.csv", index=False)

final_json = canonical_metrics_json(all_metrics_annual)
with open("final_json.json", 'w') as f:
    json.dump(final_json, f, indent=2)