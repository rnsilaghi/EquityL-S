import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # --- COMPANIES ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cik TEXT UNIQUE,
            name TEXT UNIQUE,
            ticker TEXT UNIQUE
        )
    """)

    # --- FILINGS ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            filing_date TEXT,
            filing_type TEXT,
            filing_url TEXT UNIQUE,
            is_convertible INTEGER, -- 0 or 1
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    # --- STOCK PRICES ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            date TEXT,
            close REAL,
            high REAL,
            low REAL,
            volume INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            UNIQUE(company_id, date)
        )
    """)

    # --- INTEREST RATES ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interest_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            treasury_10y REAL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
