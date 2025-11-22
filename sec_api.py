import requests
from typing import List, Dict
from config import SEC_API_KEY, SEC_BASE_URL
from db import get_connection

def fetch_sec_filings(limit: int = 100) -> List[Dict]:
    if not SEC_API_KEY or SEC_API_KEY.startswith("YOUR_"):
        raise ValueError("SEC_API_KEY missing in config.py")

    url = f"{SEC_BASE_URL}?token={SEC_API_KEY}"

    payload = {
        "query": 'formType:"8-K" AND ("convertible debt" OR "convertible notes" OR "convertible bond")',
        "from": "0",
        "size": str(limit),
        "sort": [{ "filedAt": { "order": "desc" }}]
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()

    filings: List[Dict] = []

    for item in data.get("filings", []):
        description = item.get("formDescription", "").lower() 
        if "convertible preferred" in description:
            continue 
        filings.append({
            "cik": item.get("cik"),
            "company_name": item.get("companyName"),
            "ticker": item.get("ticker"),
            "filing_date": item.get("filedAt", "")[:10],
            "filing_type": item.get("formType"),
            "filing_url": item.get("linkToHtml"),
            "is_convertible": 1
        })

    return filings


def store_sec_filings_to_db(filings: List[Dict]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    for f in filings:
        cik = f["cik"]
        name = f["company_name"]
        ticker = f.get("ticker")

        cur.execute("""
            INSERT OR IGNORE INTO companies (cik, name, ticker)
            VALUES (?, ?, ?)
        """, (cik, name, ticker))

        cur.execute("SELECT id FROM companies WHERE cik = ?", (cik,))
        company_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO filings (company_id, filing_date, filing_type, filing_url, is_convertible)
            VALUES (?, ?, ?, ?, ?)
        """, (
            company_id,
            f["filing_date"],
            f["filing_type"],
            f["filing_url"],
            f["is_convertible"]
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    test = fetch_sec_filings(limit=25)
    store_sec_filings_to_db(test)
    print(f"Inserted {len(test)} SEC filings.")