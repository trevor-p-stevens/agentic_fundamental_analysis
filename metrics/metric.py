from metrics.xbrl_map import get_metric_value, load_xbrl_map

def build_master_metrics(us_gaap_10k_list, us_gaap_10q_list, cik, accession_numbers_10k, accession_numbers_10q, primary_doc_10k, primary_doc_10q):
    xbrl_map = load_xbrl_map()
    metrics = list(xbrl_map.keys())

    def build_for_report(us_gaap_list, accession_numbers, primary_docs):
        master = {metric: [] for metric in metrics}
        for idx, us_gaap_data in enumerate(us_gaap_list):
            accession = accession_numbers[idx]
            primary_doc = primary_docs[idx]
            for metric in metrics:
                entries = get_metric_value(
                    us_gaap_data, metric,
                    cik=cik,
                    accession=accession,
                    primary_doc=primary_doc
                )
                if entries:
                    master[metric].extend(entries)
                else:
                    master[metric].append({"period_end": None, "value": None})        # Deduplicate and sort by period_end descending
        for metric in master:
            seen = set()
            unique_entries = []
            for entry in master[metric]:
                pe = entry["period_end"]
                if pe not in seen:
                    unique_entries.append(entry)
                    seen.add(pe)
            unique_entries.sort(key=lambda x: (x["period_end"] is not None, x["period_end"]), reverse=True)
            master[metric] = unique_entries
        return master

    master_10k = build_for_report(us_gaap_10k_list, accession_numbers_10k, primary_doc_10k)
    master_10q = build_for_report(us_gaap_10q_list, accession_numbers_10q, primary_doc_10q)
    return master_10k, master_10q