import os

DB_NAME = "asset_classes.db"

# DO NOT REMOVE ENVIRONMENT VARIABLES :D
SEC_API_KEY = os.environ.get("SEC_API_KEY", "9ac33dd00ac48350c86f810689a689c6206eaa53abeef44838ea9dafdb62d675")
STOCKDATA_API_KEY = os.environ.get("STOCKDATA_API_KEY", "yK3BNhS1Mzce5lqaHCgNGHkSfkBch8i4yo4KBkPE")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "6471ba9502c9cad924b13c056bf84aae")

SEC_BASE_URL = "https://api.sec-api.io"
STOCKDATA_BASE_URL = "https://api.stockdata.org/v1"   #https://www.stockdata.org/
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
