import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cik TEXT UNIQUE,
            name TEXT,
            ticker TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            filing_date TEXT,
            filing_type TEXT,
            filing_url TEXT,
            is_convertible INTEGER, -- 0 or 1
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            date TEXT,
            close REAL,
            high REAL,
            low REAL,
            volume INTEGER,
            UNIQUE(company_id, date),   -- ⭐ prevents duplicates
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interest_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            effr REAL,
            treasury_10y REAL,
            baa_yield REAL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")

#Framework for the database is complete
