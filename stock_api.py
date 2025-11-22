import requests
from datetime import datetime, timedelta
from typing import List, Dict
from config import STOCKDATA_API_KEY, STOCKDATA_BASE_URL
from db import get_connection

def fetch_stock_prices(ticker: str, filing_date: str) -> List[Dict]:
    if not ticker:
        return []

    end_date = datetime.fromisoformat(filing_date)
    start_date = end_date - timedelta(days=365)

    url = f"{STOCKDATA_BASE_URL}/data/eod"
    
    params = {
        "api_token": STOCKDATA_API_KEY,
        "symbols": ticker,
        "date_from": start_date.strftime("%Y-%m-%d"),
        "date_to": filing_date,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    prices = []
    for record in data.get("data", []):
        prices.append({
            "date": record.get("date"),
            "close": record.get("close"),
            "high": record.get("high"),
            "low": record.get("low"),
            "volume": record.get("volume")
        })

    return prices

def store_stock_prices_to_db(company_id: int, prices: List[Dict]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    for p in prices:
        cur.execute("""
            INSERT OR IGNORE INTO stock_prices (company_id, date, close, high, low, volume)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            p["date"],
            p["close"],
            p["high"],
            p["low"],
            p["volume"]
        ))

    conn.commit()
    conn.close()