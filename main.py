from db import create_tables, get_connection
from sec_api import fetch_sec_filings, store_sec_filings_to_db
from stock_api import fetch_stock_prices, store_stock_prices_to_db
from fred_api import fetch_treasury_10y, store_treasury_10y_to_db

def load_sec_data(limit: int = 25):
    print(f"Fetching up to {limit} SEC filings...")
    filings = fetch_sec_filings(limit=limit)
    store_sec_filings_to_db(filings)
    print(f"Inserted {len(filings)} SEC filings.")


def load_stock_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTI bNCT c.id, c.ticker, MIN(f.filing_date)
        FROM companies c
        JOIN filings f ON c.id = f.company_id
        WHERE c.ticker IS NOT NULL
        GROUP BY c.id, c.ticker
    """)

    rows = cur.fetchall()
    conn.close()

    for company_id, ticker, filing_date in rows:
        print(f"Fetching prices for {ticker} (company_id={company_id})...")
        prices = fetch_stock_prices(ticker, filing_date)
        store_stock_prices_to_db(company_id, prices)
        print(f"Saved {len(prices)} price records for {ticker}.")


def load_interest_rate_data(start_date: str, end_date: str, max_rows: int = 25):
    print(f"Fetching up to {max_rows} interest-rate observations from {start_date} to {end_date}...")
    rates = fetch_treasury_10y(start_date=start_date, end_date=end_date, max_rows=max_rows)
    store_treasury_10y_to_db(rates)
    print(f"Inserted {len(rates)} interest-rate rows.")


def main():
    # 1. Make sure tables exist
    create_tables()

    # 2. Uncomment the pieces you want to run in a given execution

    # Step A: Load SEC data (max 25 filings per run)
    load_sec_data(limit=25)

    # Step B: Load stock data for companies already in DB
    # load_stock_data()

    # Step C: Load FRED interest-rate data (e.g. last few years)
    # load_interest_rate_data(start_date="2015-01-01", end_date="2024-12-31", max_rows=25)

    print("main.py finished. Uncomment functions in main() to run specific data loads.")


if __name__ == "__main__":
    main()