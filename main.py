# main.py

from db import create_tables, get_connection
from sec_api import fetch_sec_filings, store_sec_filings_to_db
from stock_api import fetch_stock_prices, store_stock_prices_to_db
from fred_api import fetch_treasury_10y, store_treasury_10y_to_db

# ========== SEC ==========
def load_sec_data(limit: int = 25):
    print(f"\n📥 Fetching up to {limit} SEC filings...")
    filings = fetch_sec_filings(limit=limit)
    store_sec_filings_to_db(filings)
    print(f"✔ Inserted {len(filings)} SEC filings.\n")


# ========== STOCK PRICES ==========
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

    rows = cur.fetchall()
    conn.close()

    for company_id, ticker, filing_date in rows:
        print(f"Fetching stock prices for {ticker} (company_id={company_id})...")
        prices = fetch_stock_prices(ticker, filing_date)
        store_stock_prices_to_db(company_id, prices)
        print(f"Saved {len(prices)} daily price records.\n")


# ========== FRED ==========
def load_interest_rate_data(start_years_back: int = 10, max_rows: int = 50):
    print(f"\nFetching up to {max_rows} Treasury 10Y interest rates...")
    rates = fetch_treasury_10y(start_years_back=start_years_back, max_rows=max_rows)
    store_treasury_10y_to_db(rates)
    print(f"✔ Inserted {len(rates)} interest-rate rows.\n")


# ======================================================
# ===================== MAIN FLOW ======================
# ======================================================
def main():
    print("🔧 Initializing database...")
    create_tables()

    # A) Fetch SEC convertible bond filings
    #load_sec_data(limit=25)

    # B) Fetch stock prices for companies already in DB
    #load_stock_data()

    # C) Fetch interest-rate history (only 10Y)
    load_interest_rate_data(start_years_back=5, max_rows=100)

    print("🎉 main.py finished. Uncomment steps to run specific loads.")

if __name__ == "__main__":
    main()