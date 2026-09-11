"""
Part 2a: Load saas_companies_clean.csv, company_investors.csv (from prepare_data.py),
and stock_prices.csv / stock_analytics.csv (from Part 1) into a
local SQLite database, saas_companies.db, using schema.sql.
"""
import sqlite3
import pandas as pd
import os

DB_PATH = "saas_companies.db"
SCHEMA_PATH = "schema.sql"
COMPANIES_CSV = "saas_companies_clean.csv"
INVESTORS_CSV = "company_investors.csv"
PRICES_CSV = "stock_prices.csv"
ANALYTICS_CSV = "stock_analytics.csv"


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(SCHEMA_PATH) as f:
        cur.executescript(f.read())

    # Load companies 
    if not os.path.exists(COMPANIES_CSV):
        print(f"ERROR: {COMPANIES_CSV} not found — run prepare_part2_data.py first.")
        conn.close()
        return

    df = pd.read_csv(COMPANIES_CSV)
    rename_map = {
        "Company Name": "company_name",
        "Founded Year": "founded_year",
        "HQ": "hq",
        "Industry": "industry",
        "industry_bucket": "industry_bucket",
        "Total Funding": "total_funding",
        "ARR": "arr",
        "Valuation": "valuation",
        "total_funding_usd": "total_funding_usd",
        "arr_usd": "arr_usd",
        "Employees": "employees",
        "Top Investors": "top_investors",
        "Product": "product",
        "G2 Rating": "g2_rating",
        "Ticker": "ticker",
        "Exchange": "exchange",
        "Status": "status",
        "Notes": "notes",
    }
    df = df.rename(columns=rename_map)
    cols = list(rename_map.values())
    df[cols].to_sql("companies", conn, if_exists="append", index=False)
    print(f"Loaded {len(df)} companies into 'companies' table.")

    # Load company_investors junction table
    if os.path.exists(INVESTORS_CSV):
        investors = pd.read_csv(INVESTORS_CSV)
        investors[["company_name", "investor_name"]].to_sql(
            "company_investors", conn, if_exists="append", index=False
        )
        print(f"Loaded {len(investors)} company-investor pairs into 'company_investors' table.")
    else:
        print(f"No {INVESTORS_CSV} found yet — run prepare_part2_data.py first.")

    # Load stock prices
    if os.path.exists(PRICES_CSV):
        prices = pd.read_csv(PRICES_CSV)
        expected = ["ticker", "trade_date", "open", "high", "low", "close", "adj_close",
                    "volume", "shares_outstanding", "market_cap"]
        missing = set(expected) - set(prices.columns)
        if missing:
            print(f"WARNING: stock_prices.csv is missing columns {missing}; skipping load.")
        else:
            prices[expected].to_sql("stock_prices", conn, if_exists="append", index=False)
            print(f"Loaded {len(prices)} price rows into 'stock_prices' table.")
    else:
        print("No stock_prices.csv found yet — run pull_stock_history.py first "
              "(in an environment with internet access) to generate it, then re-run this loader.")

    # Load stock analytics (TSR / market cap CAGR)
    if os.path.exists(ANALYTICS_CSV):
        analytics = pd.read_csv(ANALYTICS_CSV)
        expected = ["ticker", "company_name", "industry", "product", "last_known_valuation",
                    "as_of_date", "years_of_data", "has_3y_history", "current_price",
                    "shares_outstanding", "current_market_cap", "tsr_1y", "tsr_3y",
                    "market_cap_3y_ago", "market_cap_cagr_3y"]
        missing = set(expected) - set(analytics.columns)
        if missing:
            print(f"WARNING: stock_analytics.csv is missing columns {missing}; skipping load.")
        else:
            analytics[expected].to_sql("stock_analytics", conn, if_exists="append", index=False)
            print(f"Loaded {len(analytics)} rows into 'stock_analytics' table.")
    else:
        print("No stock_analytics.csv found yet — run calculate_tsr_market_cap.py after "
              "pull_stock_history.py, then re-run this loader.")

    conn.commit()
    conn.close()
    print(f"\nDone. Database written to {DB_PATH}")


if __name__ == "__main__":
    main()