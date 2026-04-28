import requests

HEADERS = {
    "User-Agent": "fundamental analysis agent trevorstevensp@gmail.com"
}

def get_cik(ticker: str):
    url = "https://www.sec.gov/files/company_tickers.json"
    data = requests.get(url, headers=HEADERS).json()

    for company in data.values():
        if company["ticker"].lower() == ticker.lower():
            cik = str(company["cik_str"]).zfill(10)
            return cik

    return None


cik = get_cik("AAPL")
print("CIK:", cik)