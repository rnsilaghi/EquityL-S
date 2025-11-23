# Your names: Robert Silaghi 
# Your student ids: 87125192 
# Your emails: silaghi@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT): ChatGPT
# If you worked with generative AI also add a statement for how you used it.  
# We used ChatGPT for debugging all of our files other than config.py. We also used it to create our database structure in db.py. We also used it to make sure our variables are unique. We also used it to understand packages like datetime and delta. We also used it for some SQL commands like insert or ignore. We also used it for help for limiting our API call. We also used it for methods like .isoformat(). We also used it to give us print statements to use in debugging. Lastly, we used it for date related methods like .strftime().


from db import create_tables
from db import create_tables
from pipeline import load_sec_data, load_and_store_stock_returns, load_interest_rate_data
from analysis import run_analysis

def main():
    print("Initializing database...")
    create_tables()

    # A) Fetch SEC convertible bond filings
    load_sec_data(limit=25)

    # B) Fetch stock prices for companies already in DB
    load_and_store_stock_returns()

    # C) Fetch interest-rate history (only 10Y)
    load_interest_rate_data(start_years_back=5, max_rows=99999)

    # D) Run analysis
    run_analysis()

    print("main.py finished.")

if __name__ == "__main__":
    main()