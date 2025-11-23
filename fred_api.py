import requests
from typing import List, Dict
from datetime import datetime, timedelta
from config import FRED_API_KEY, FRED_BASE_URL
from db import get_connection

FRED_SERIES = "DGS10"

def fetch_treasury_10y(start_years_back: int = 5, max_rows: int = 25) -> List[Dict]:
    if not FRED_API_KEY or FRED_API_KEY.startswith("YOUR_"):
        raise ValueError("FRED_API_KEY missing in config.py")

    end_date = datetime.today()
    start_date = end_date - timedelta(days=365 * start_years_back)

    url = f"{FRED_BASE_URL}/series/observations"

    params = {
        "api_key": FRED_API_KEY,
        "series_id": FRED_SERIES,
        "file_type": "json",
        "observation_start": start_date.strftime("%Y-%m-%d"),
        "observation_end": end_date.strftime("%Y-%m-%d")
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    rows: List[Dict] = []

    for obs in data.get("observations", []):
        value_str = obs.get("value")

        try:
            value = float(value_str) if value_str not in (None, ".", "") else None
    
        except ValueError:
            value = None

        rows.append({
            "date": obs.get("date"),
            "treasury_10y": value
        })

    rows = sorted(rows, key=lambda r: datetime.fromisoformat(r["date"]))[:max_rows]
    
    return rows


def store_treasury_10y_to_db(rates: List[Dict]) -> None:
    if not rates:
        print("No interest-rate data to store.")
        return

    conn = get_connection()
    cur = conn.cursor()

    for r in rates:
        cur.execute("""
            INSERT OR IGNORE INTO interest_rates (date, treasury_10y)
            VALUES (?, ?)
        """, (r["date"], r["treasury_10y"]))

    conn.commit()
    conn.close()