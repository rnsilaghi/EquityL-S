import requests
from typing import List, Dict
from datetime import datetime
from config import FRED_API_KEY, FRED_BASE_URL
from db import get_connection

FRED_SERIES = {
    "effr": "FEDFUNDS",
    "treasury_10y": "DGS10",
    "baa_yield": "BAA"
}

def _fetch_single_series(series_id: str, start_date: str, end_date: str) -> Dict[str, float]:
    url = f"{FRED_BASE_URL}/series/observations"

    params = {
        "api_key": FRED_API_KEY,
        "series_id": series_id,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    out: Dict[str, float] = {}

    for obs in data.get("observations", []):
        date = obs.get("date")
        value_str = obs.get("value")
        if value_str in (None, ".", ""):
            value = None
        else:
            try:
                value = float(value_str)
            except ValueError:
                value = None
        out[date] = value

    return out


def fetch_interest_rates(start_date: str, end_date: str, max_rows: int = 25) -> List[Dict]:
    if not FRED_API_KEY or FRED_API_KEY.startswith("YOUR_"):
        raise ValueError("FRED_API_KEY missing in config.py")    
    
    effr_map = _fetch_single_series(FRED_SERIES["effr"], start_date, end_date)
    t10_map = _fetch_single_series(FRED_SERIES["treasury_10y"], start_date, end_date)
    baa_map = _fetch_single_series(FRED_SERIES["baa_yield"], start_date, end_date)

    all_dates = sorted(
        set(effr_map.keys()) | set(t10_map.keys()) | set(baa_map.keys()),
        key=lambda d: datetime.fromisoformat(d)
    )

    all_dates = all_dates[:max_rows]

    rows: List[Dict] = []
    for d in all_dates:
        rows.append({
            "date": d,
            "effr": effr_map.get(d),
            "treasury_10y": t10_map.get(d),
            "baa_yield": baa_map.get(d),
        })

    return rows

def store_interest_rates_to_db(rates: List[Dict]) -> None:
    if not rates:
        print("⚠️ No interest-rate data to store.")
        return

    conn = get_connection()
    cur = conn.cursor()

    for r in rates:
        cur.execute("""
            INSERT INTO interest_rates (date, effr, treasury_10y, baa_yield)
            VALUES (?, ?, ?, ?)
        """, (
            r["date"],
            r["effr"],
            r["treasury_10y"],
            r["baa_yield"]
        ))

    conn.commit()
    conn.close()