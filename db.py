# db.py
import sqlite3
from config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # COMPANIES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            cik TEXT UNIQUE,
            name TEXT,
            ticker TEXT UNIQUE
        )
    """)

    # FILINGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            filing_date TEXT,
            filing_type TEXT,
            filing_url TEXT UNIQUE,
            is_convertible INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    # STOCK PRICES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_returns (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            filing_date TEXT,
            return_day0_to_day5 REAL,
            return_day5_to_day10 REAL,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            UNIQUE(company_id, filing_date)
        )
    """)

    # INTEREST RATES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interest_rates (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE,
            treasury_10y REAL
        )
    """)

    # METADATA
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()