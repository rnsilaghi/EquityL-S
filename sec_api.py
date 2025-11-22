import requests
import sqlite3
from typing import List, Dict
from config import SEC_API_KEY, SEC_BASE_URL, DB_NAME
from db import get_connection

def fetch_sec_filings(limit: int = 25) -> List[Dict]:
    