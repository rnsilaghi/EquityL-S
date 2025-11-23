import requests
from typing import List, Dict
from config import SEC_API_KEY, SEC_BASE_URL
from db import get_connection

def get_offset() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM metadata WHERE key = 'offset'")
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row else 0

def save_offset(offset: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO metadata (key, value) VALUES ('offset', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (str(offset),))
    conn.commit()
    conn.close()

def fetch_sec_filings(limit: int = 25) -> List[Dict]:
    if not SEC_API_KEY or SEC_API_KEY.startswith("YOUR_"):
        raise ValueError("SEC_API_KEY missing in config.py")

    # Read where we last left off
    offset = get_offset()

    url = f"{SEC_BASE_URL}?token={SEC_API_KEY}"

    payload = {
        "query": (
            'formType:"8-K" AND ('
            '"convertible debt" OR '
            '"convertible note" OR '
            '"convertible notes" OR '
            '"convertible bond" OR '
            '"convertible bonds"'
            ")"
        ),
        "from": str(offset),
        "size": str(limit),
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()

    filings: List[Dict] = []

    for item in data.get("filings", []):
        description = item.get("formDescription", "").lower()
        
        if "convertible preferred" in description:
            continue

        raw_name = item.get("companyName", "") or ""
        clean_name = " ".join(w.capitalize() for w in raw_name.split())

        filings.append({
            "cik": item.get("cik"),
            "company_name": clean_name,
            "ticker": item.get("ticker"),
            "filing_date": item.get("filedAt", "")[:10],
            "filing_type": item.get("formType"),
            "filing_url": item.get("linkToHtml"),
            "is_convertible": 1
        })

    # Save next offset
    save_offset(offset + limit)

    return filings


def store_sec_filings_to_db(filings: List[Dict]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    for f in filings:
        cik = f["cik"]
        name = f["company_name"]
        ticker = f.get("ticker")

        # Insert company (ignore if already exists)
        cur.execute("""
            INSERT OR IGNORE INTO companies (cik, name, ticker)
            VALUES (?, ?, ?)
        """, (cik, name, ticker))

        # Fetch company_id
        cur.execute("SELECT id FROM companies WHERE cik = ?", (cik,))
        row = cur.fetchone()
        if not row:
            print(f"Could not find company_id for CIK {cik}, skipping filing.")
            continue
        company_id = row[0]

        # Insert filing (ignore if accession_number already exists)
        cur.execute("""
            INSERT OR IGNORE INTO filings 
            (company_id, filing_date, filing_type, filing_url, is_convertible)
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