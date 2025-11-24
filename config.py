import os

DB_NAME = "asset_classes.db"

# DO NOT REMOVE ENVIRONMENT VARIABLES :D
SEC_API_KEY = os.environ.get("SEC_API_KEY", "INSERT HERE")
STOCKDATA_API_KEY = os.environ.get("STOCKDATA_API_KEY", "INSERT HERE")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "INSERT HERE")

SEC_BASE_URL = "https://api.sec-api.io"
STOCKDATA_BASE_URL = "https://api.stockdata.org/v1"   #https://www.stockdata.org/
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
