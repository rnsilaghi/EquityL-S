from datetime import datetime
from collections import defaultdict
from statistics import mean
import sqlite3
import matplotlib.pyplot as plt

from db import get_connection


# =========================
# === HELPER FUNCTIONS ====
# =========================

def load_interest_rates():
    """
    Load all interest-rate observations from the DB,
    return as a list of (date, treasury_10y) tuples sorted by date.
    date is a datetime.date object, treasury_10y is a float.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, treasury_10y
        FROM interest_rates
        WHERE treasury_10y IS NOT NULL
        ORDER BY date
    """)
    rows = cur.fetchall()
    conn.close()

    rates = []
    for date_str, value in rows:
        try:
            d = datetime.fromisoformat(date_str).date()
            rates.append((d, float(value)))
        except Exception:
            # Skip malformed rows
            continue

    return rates


def get_latest_rate_on_or_before(target_date, rates):
    """
    Given a target_date (datetime.date) and a list of (date, rate) sorted by date,
    return the latest rate on or before that date.
    If none exists, return None.
    """
    latest = None
    for d, r in rates:
        if d <= target_date:
            latest = r
        else:
            # Because rates are sorted ascending, once d > target_date we can stop
            break
    return latest


# =========================================
# === ANALYSIS 1: RATE ENVIRONMENTS =======
# =========================================

def calculate_filings_by_rate_bucket():
    """
    Categorize each filing based on the 10Y Treasury yield at (or just before) its filing date.

    Buckets:
        - Low (< 2%)
        - Medium (2% - 4%)
        - High (>= 4%)

    Returns a dict: {bucket_label: count_of_filings}
    """
    rates = load_interest_rates()
    if not rates:
        print("No interest-rate data found in DB.")
        return {}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filing_date FROM filings")
    filings = cur.fetchall()
    conn.close()

    buckets = defaultdict(int)

    for filing_id, filing_date_str in filings:
        try:
            filing_date = datetime.fromisoformat(filing_date_str).date()
        except Exception:
            # Skip malformed dates
            continue

        rate = get_latest_rate_on_or_before(filing_date, rates)
        if rate is None:
            # No rate available on or before this date
            continue

        if rate < 2.0:
            bucket = "Low (<2%)"
        elif rate < 4.0:
            bucket = "Medium (2–4%)"
        else:
            bucket = "High (≥4%)"

        buckets[bucket] += 1

    return dict(buckets)


def plot_filings_by_rate_bucket(bucket_counts):
    """
    Bar chart: number of convertible filings by interest-rate environment.
    """
    if not bucket_counts:
        print("No bucket counts to plot.")
        return

    labels = list(bucket_counts.keys())
    values = [bucket_counts[b] for b in labels]

    plt.figure(figsize=(8, 5), dpi=120)
    plt.bar(labels, values)
    plt.title("Number of Convertible Filings by 10Y Treasury Yield Environment")
    plt.xlabel("10Y Yield Bucket at Filing Date")
    plt.ylabel("Number of Filings")

    for i, v in enumerate(values):
        plt.text(i, v + 0.1, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("fig1_filings_by_rate_bucket.png", bbox_inches="tight")
    plt.show()


# =========================================
# === ANALYSIS 2: STOCK PERFORMANCE =======
# =========================================

def calculate_stock_window_returns():
    """
    Approximate stock performance around the earliest convertible filing per company.

    Because we do NOT always have a full ±30-day window, we:
    - For each company, identify its earliest filing.
    - Grab all stock_prices rows for that company.
    - Compute a simple return between the first available close and last available close
      in our stored window:

          return_pct = (last_close - first_close) / first_close * 100

    We also attach the 10Y yield at the filing date (or most recent prior).

    Returns a list of dicts with keys:
        'filing_id', 'ticker', 'filing_date', 'start_date', 'end_date',
        'start_close', 'end_close', 'return_pct', 'rate_at_filing'
    """
    rates = load_interest_rates()
    if not rates:
        print("No interest-rate data found for stock-return analysis.")
        return []

    conn = get_connection()
    cur = conn.cursor()

    # Only match stock prices to the earliest filing for each company
    cur.execute("""
        SELECT f.id,
               f.company_id,
               f.filing_date,
               c.ticker,
               sp.date,
               sp.close
        FROM filings f
        JOIN companies c ON f.company_id = c.id
        JOIN stock_prices sp ON sp.company_id = c.id
        WHERE f.filing_date = (
            SELECT MIN(f2.filing_date)
            FROM filings f2
            WHERE f2.company_id = f.company_id
        )
        ORDER BY f.id, sp.date
    """)
    rows = cur.fetchall()
    conn.close()

    # Group by filing_id
    data_by_filing = defaultdict(list)
    meta_by_filing = {}

    for filing_id, company_id, filing_date_str, ticker, price_date_str, close_price in rows:
        meta_by_filing[filing_id] = (filing_date_str, ticker)
        data_by_filing[filing_id].append((price_date_str, close_price))

    results = []

    for filing_id, price_rows in data_by_filing.items():
        filing_date_str, ticker = meta_by_filing[filing_id]

        # Convert, sort by date
        cleaned = []
        for date_str, close in price_rows:
            try:
                d = datetime.fromisoformat(date_str).date()
                if close is not None:
                    cleaned.append((d, float(close)))
            except Exception:
                continue

        if len(cleaned) < 2:
            # Not enough data to compute a change
            continue

        cleaned.sort(key=lambda x: x[0])
        start_date, start_close = cleaned[0]
        end_date, end_close = cleaned[-1]

        if start_close == 0:
            continue

        return_pct = (end_close - start_close) / start_close * 100.0

        try:
            filing_date = datetime.fromisoformat(filing_date_str).date()
        except Exception:
            filing_date = None

        rate = None
        if filing_date is not None:
            rate = get_latest_rate_on_or_before(filing_date, rates)

        results.append({
            "filing_id": filing_id,
            "ticker": ticker,
            "filing_date": filing_date_str,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "start_close": start_close,
            "end_close": end_close,
            "return_pct": return_pct,
            "rate_at_filing": rate
        })

    return results


def plot_return_vs_rate(stock_results):
    """
    Scatter plot: approximate stock return vs 10Y yield at filing.

    X-axis: 10Y Treasury yield at (or just before) filing date
    Y-axis: simple return (in %) from first to last available close in our window
    """
    if not stock_results:
        print("No stock return data to plot.")
        return

    x = []
    y = []
    labels = []

    for r in stock_results:
        if r["rate_at_filing"] is None:
            continue
        x.append(r["rate_at_filing"])
        y.append(r["return_pct"])
        labels.append(r["ticker"])

    if not x:
        print("No observations with both returns and rates.")
        return

    plt.figure(figsize=(8, 5), dpi=120)
    plt.scatter(x, y)
    plt.title("Stock Performance Around Convertible Filing vs 10Y Yield")
    plt.xlabel("10Y Treasury Yield at Filing Date (%)")
    plt.ylabel("Approx. Return from First to Last Available Close (%)")

    # Optionally annotate a few points (up to 10)
    for i in range(min(10, len(x))):
        plt.annotate(labels[i], (x[i], y[i]), xytext=(3, 3),
                     textcoords="offset points", fontsize=8)

    plt.axhline(0, linestyle="--")  # zero-return line
    plt.tight_layout()
    plt.savefig("fig2_return_vs_rate_scatter.png", bbox_inches="tight")
    plt.show()


# =========================================
# === ANALYSIS 3: FILINGS OVER TIME =======
# =========================================

def calculate_filings_per_month():
    """
    Count how many filings occur in each year-month (YYYY-MM).
    Returns a list of (year_month, count) sorted by year_month.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT substr(filing_date, 1, 7) AS ym,
               COUNT(*)
        FROM filings
        GROUP BY ym
        ORDER BY ym
    """)
    rows = cur.fetchall()
    conn.close()

    # Filter out any None/empty ym
    return [(ym, count) for ym, count in rows if ym]


def plot_filings_over_time(ym_counts):
    """
    Line plot: number of filings per month over time.
    """
    if not ym_counts:
        print("No monthly filing data to plot.")
        return

    labels = [row[0] for row in ym_counts]
    values = [row[1] for row in ym_counts]

    plt.figure(figsize=(10, 5), dpi=120)
    plt.plot(labels, values, marker="o")
    plt.title("Convertible Filings Over Time (by Month)")
    plt.xlabel("Year-Month")
    plt.ylabel("Number of Filings")
    plt.xticks(rotation=45, ha="right")

    for i, v in enumerate(values):
        plt.text(i, v + 0.1, str(v), ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig("fig3_filings_over_time.png", bbox_inches="tight")
    plt.show()


# =========================================
# === SUMMARY OUTPUT TO TEXT FILE =========
# =========================================

def write_summary_to_file(bucket_counts, stock_results, ym_counts,
                          filename="analysis_summary.txt"):
    """
    Write a plain-text summary of key calculations to a file.
    This is handy for the "write calculated data to a file" bonus and for your report.
    """
    with open(filename, "w") as f:
        f.write("=== SI 201 Final Project – Analysis Summary ===\n\n")

        # Filings by rate environment
        f.write("1) Filings by 10Y Treasury Yield Environment\n")
        if bucket_counts:
            total_filings = sum(bucket_counts.values())
            for bucket, count in bucket_counts.items():
                pct = (count / total_filings) * 100 if total_filings else 0
                f.write(f"   - {bucket}: {count} filings ({pct:.1f}%)\n")
            f.write(f"   Total filings considered: {total_filings}\n\n")
        else:
            f.write("   No data available.\n\n")

        # Stock returns
        f.write("2) Approximate Stock Performance Around Convertible Filings\n")
        if stock_results:
            returns = [r["return_pct"] for r in stock_results]
            avg_ret = mean(returns)
            min_ret = min(returns)
            max_ret = max(returns)
            f.write(f"   Number of companies with usable price data: {len(stock_results)}\n")
            f.write(f"   Average return across window: {avg_ret:.2f}%\n")
            f.write(f"   Min return: {min_ret:.2f}%\n")
            f.write(f"   Max return: {max_ret:.2f}%\n\n")
        else:
            f.write("   No usable stock price data available.\n\n")

        # Filings over time
        f.write("3) Filings Over Time (by Month)\n")
        if ym_counts:
            for ym, count in ym_counts:
                f.write(f"   - {ym}: {count} filings\n")
            f.write("\n")
        else:
            f.write("   No filings aggregated by month.\n\n")

    print(f"Summary written to {filename}")

# =========================================
# ============== MAIN =====================
# =========================================

def main():
    # 1) Filings by rate bucket
    bucket_counts = calculate_filings_by_rate_bucket()
    print("Filings by rate bucket:", bucket_counts)
    plot_filings_by_rate_bucket(bucket_counts)

    # 2) Stock performance vs rate
    stock_results = calculate_stock_window_returns()
    print(f"Computed stock-window returns for {len(stock_results)} filings.")
    plot_return_vs_rate(stock_results)

    # 3) Filings per month
    ym_counts = calculate_filings_per_month()
    print("Filings per month:", ym_counts)
    plot_filings_over_time(ym_counts)

    # 4) Write summary to text file (bonus + report helper)
    write_summary_to_file(bucket_counts, stock_results, ym_counts)


if __name__ == "__main__":
    main()