from stock_api import fetch_stock_prices, store_stock_prices_to_db
from db import get_connection

def load_stock_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT c.id, c.ticker, MIN(f.filing_date)
        FROM companies c
        JOIN filings f ON c.id = f.company_id
        WHERE c.ticker IS NOT NULL
        GROUP BY c.id, c.ticker
    """)

    for company_id, ticker, filing_date in cur.fetchall():
        print(f"📈 Fetching prices for {ticker}...")
        prices = fetch_stock_prices(ticker, filing_date)
        store_stock_prices_to_db(company_id, prices)
        print(f"   ✔ Saved {len(prices)} records.")

    conn.close()

def main():
    create_tables()
    # load_sec_data()   # Do NOT uncomment unless you need more SEC data
    load_stock_data()   # ⭐ LOAD STOCK PRICES HERE
    print("🎉 Done loading stock data!")