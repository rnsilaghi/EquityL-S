from db import get_connection
from datetime import datetime
from collections import defaultdict
import sqlite3
import matplotlib.pyplot as plt
from statistics import median

def load_interest_rates():
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
            continue

    return rates


def get_latest_rate_on_or_before(target_date, rates):
    latest = None
    
    for d, r in rates:
        
        if d <= target_date:
            latest = r
        
        else:
            # Because rates are sorted ascending, once d > target_date we can stop
            break

    return latest



# FILINGS BY RATE BUCKET

def calculate_filings_by_rate_bucket():
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
            # Skip weird dates
            continue

        rate = get_latest_rate_on_or_before(filing_date, rates)
        
        if rate is None:
            # No rate available on or before this date
            continue

        if rate < 2.0:
            bucket = "Low (<2%)"
        elif rate < 4.0:
            bucket = "Medium (2-4%)"
        else:
            bucket = "High (>=4%)"

        buckets[bucket] += 1

    return dict(buckets)


def plot_filings_by_rate_bucket(bucket_counts):
    if not bucket_counts:
        print("No bucket counts to plot.")
        return

    labels = list(bucket_counts.keys())
    values = [bucket_counts[b] for b in labels]

    plt.figure(figsize=(10, 5), dpi=140)
    plt.bar(labels, values)
    
    plt.title("Number of Convertible Filings by 10Y Treasury Yield Environment")
    plt.xlabel("10Y Yield Bucket at Filing Date")
    plt.ylabel("Number of Filings")

    for i, v in enumerate(values):
        plt.text(i, v + 0.1, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("fig1_filings_by_rate_bucket.png", bbox_inches="tight")
    plt.show()


# FILINGS OVER TIME
def calculate_filings_per_month():
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
    if not ym_counts:
        print("No monthly filing data to plot.")
        return

    labels = [row[0] for row in ym_counts]
    values = [row[1] for row in ym_counts]

    plt.figure(figsize=(10, 5), dpi=140)
    plt.plot(labels, values, marker="o")
    
    plt.title("Convertible Filings Over Time (by Month)")
    plt.xlabel("Year-Month")
    plt.ylabel("Number of Filings")
    plt.xticks(rotation=45, ha="right")

    for i, v in enumerate(values):
        plt.text(i, v + 0.1, str(v), ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig("fig2_filings_over_time.png", bbox_inches="tight")
    plt.show()

# AVERAGE RETURNS FOR DAY0 to 5 and 5 to 10 

def load_compact_stock_returns():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.ticker, r.filing_date, r.return_day0_to_day5, r.return_day5_to_day10
        FROM stock_returns r
        JOIN companies c ON r.company_id = c.id
    """)
    
    rows = cur.fetchall()
    conn.close()

    results = []
    for ticker, filing_date, r0_5, r5_10 in rows:
    
        try:
            r0_5_val = float(r0_5) if r0_5 is not None else None
    
        except Exception:
            r0_5_val = None
    
        try:
            r5_10_val = float(r5_10) if r5_10 is not None else None
    
        except Exception:
            r5_10_val = None

        results.append((ticker, filing_date, r0_5_val, r5_10_val))

    return results


def calculate_avg_returns():
    rows = load_compact_stock_returns()
    r0_5_list = []
    r5_10_list = []

    for _, _, r0_5, r5_10 in rows:
    
        if r0_5 is not None:
            r0_5_list.append(r0_5)
    
        if r5_10 is not None:
            r5_10_list.append(r5_10)

    avg0_5 = median(r0_5_list) if r0_5_list else None
    avg5_10 = median(r5_10_list) if r5_10_list else None

    return {
        "avg_day0_5": avg0_5,
        "avg_day5_10": avg5_10,
        "count_day0_5": len(r0_5_list),
        "count_day5_10": len(r5_10_list)
    }

def plot_avg_returns_bar(avg_stats):
    avg0 = avg_stats.get("avg_day0_5")
    avg5 = avg_stats.get("avg_day5_10")

    labels = ["Day0 → Day5", "Day5 → Day10"]
    values = [avg0 if avg0 is not None else 0.0, avg5 if avg5 is not None else 0.0]

    plt.figure(figsize=(10, 5), dpi=140)
    bars = plt.bar(labels, values)
    plt.title("Median Returns Around Convertible Filing")
    plt.ylabel("Median Return (%)")

    # Annotate bars with values or 'N/A'
    for i, b in enumerate(bars):
        val = values[i]
        
        if (i == 0 and avg0 is None) or (i == 1 and avg5 is None):
            txt = "N/A"
        
        else:
            txt = f"{val:.2f}%"
        
        plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05, txt,
                 ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig("fig3_avg_returns_bar.png", bbox_inches="tight")
    plt.show()


# SUMMARY OUTPUT TO TEXT FILE

def write_summary_to_file(bucket_counts, avg_stats, ym_counts, filename="analysis_summary.txt"):
    # Helper to normalize labels, def inside def
    
    def normalize_label(s: str) -> str:
    
        if not isinstance(s, str):
            return str(s)
    
        return s.replace("–", "-").replace("—", "-").replace("≥", ">=").replace("≤", "<=")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("=== SI 201 Final Project – Analysis Summary ===\n\n")

        # Filings by rate environment
        f.write("1) Filings by 10Y Treasury Yield Environment\n")
        
        if bucket_counts:
            total_filings = sum(bucket_counts.values())
        
            for bucket, count in bucket_counts.items():
                pct = (count / total_filings) * 100 if total_filings else 0
                safe_bucket = normalize_label(bucket)
                f.write(f"   - {safe_bucket}: {count} filings ({pct:.1f}%)\n")
        
            f.write(f"   Total filings considered (for rate buckets): {total_filings}\n\n")
        
        else:
            f.write("   No data available.\n\n")

        # Average returns
        f.write("2) Average Returns Around Convertible Filings\n")
        
        if avg_stats:
            a0 = avg_stats.get("avg_day0_5")
            a5 = avg_stats.get("avg_day5_10")
            c0 = avg_stats.get("count_day0_5", 0)
            c5 = avg_stats.get("count_day5_10", 0)
        
            if a0 is not None:
                f.write(f"   - Day0 → Day5: {a0:.2f}% (n={c0})\n")
        
            else:
                f.write(f"   - Day0 → Day5: N/A (n={c0})\n")
        
            if a5 is not None:
                f.write(f"   - Day5 → Day10: {a5:.2f}% (n={c5})\n")
        
            else:
                f.write(f"   - Day5 → Day10: N/A (n={c5})\n")
        
            f.write("\n")
        
        else:
            f.write("   No stock return data available.\n\n")

        # Filings over time
        f.write("3) Filings Over Time (by Month)\n")
        
        if ym_counts:
        
            for ym, count in ym_counts:
                f.write(f"   - {ym}: {count} filings\n")
            f.write("\n")
        
        else:
            f.write("   No filings aggregated by month.\n\n")

    print(f"Summary written to {filename}")

# RUN
def run_analysis():
    # Filings by rate bucket (bar chart)
    bucket_counts = calculate_filings_by_rate_bucket()
    print("Filings by rate bucket:", bucket_counts)
    plot_filings_by_rate_bucket(bucket_counts)

    # Average returns (two-bar chart)
    avg_stats = calculate_avg_returns()
    print("Average return stats:", avg_stats)
    plot_avg_returns_bar(avg_stats)

    # Filings per month (line chart)
    ym_counts = calculate_filings_per_month()
    print("Filings per month:", ym_counts)
    plot_filings_over_time(ym_counts)

    # Write summary file
    write_summary_to_file(bucket_counts, avg_stats, ym_counts)