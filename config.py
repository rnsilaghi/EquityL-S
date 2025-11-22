import os

DB_NAME = "asset_classes.db"

SEC_API_KEY = os.environ.get("SEC_API_KEY", "cd987be4425e8c3064ce4d602f913b3edc27a1af91be9396fbc377055fc2e0de")
STOCKDATA_API_KEY = os.environ.get("STOCKDATA_API_KEY", "MRexJ4p6r1G4c0u1wpB2ESUlZUg0qAUp7x9hrHJB")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "6471ba9502c9cad924b13c056bf84aae")

SEC_BASE_URL = "https://api.sec-api.io"
STOCKDATA_BASE_URL = "https://api.stockdata.org/v1"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
