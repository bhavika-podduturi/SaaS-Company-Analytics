"""
Part 1a: Import stock price and shares outstanding data over 3 years 
for each public company in the Top 100 SaaS Companies dataset.

Part 1b: Use stock price and shares outstanding data to calculate 
1-Year TSR, 3-Year TSR, and Market Cap trends, 
providing insights to retail investors.
"""

import pandas as pd

PRICES_CSV = "stock_prices.csv"
COMPANIES_CSV = "saas_companies_enriched.csv"
OUTPUT_CSV = "stock_analytics.csv"

TRADING_DAYS_PER_YEAR = 252


def nearest_row_on_or_before(group: pd.DataFrame, target_date: pd.Timestamp) -> pd.Series:
    """Given a ticker's price history (sorted by trade_date) and a target date,
    return the row with the latest trade_date <= target_date, or None if no
    such row exists (i.e. history doesn't go back that far)."""
    eligible = group[group["trade_date"] <= target_date]
    if eligible.empty:
        return None
    return eligible.iloc[-1]


def compute_metrics_for_ticker(ticker: str, group: pd.DataFrame) -> dict:
    group = group.sort_values("trade_date").reset_index(drop=True)

    latest = group.iloc[-1]
    latest_date = latest["trade_date"]
    years_of_data = (latest_date - group.iloc[0]["trade_date"]).days / 365.25

    row_1y_ago = nearest_row_on_or_before(group, latest_date - pd.DateOffset(years=1))
    row_3y_ago = nearest_row_on_or_before(group, latest_date - pd.DateOffset(years=3))

    result = {
        "ticker": ticker,
        "as_of_date": latest_date.date(),
        "years_of_data": round(years_of_data, 2),
        "has_3y_history": years_of_data >= 2.95,  # small buffer for weekends/holidays at pull time
        "current_price": latest["close"],
        "shares_outstanding": latest["shares_outstanding"],
        "current_market_cap": latest["market_cap"],
        "tsr_1y": None,
        "tsr_3y": None,
        "market_cap_3y_ago": None,
        "market_cap_cagr_3y": None,
    }

    if row_1y_ago is not None and row_1y_ago["adj_close"]:
        result["tsr_1y"] = (latest["adj_close"] / row_1y_ago["adj_close"]) - 1

    if row_3y_ago is not None and row_3y_ago["adj_close"]:
        result["tsr_3y"] = (latest["adj_close"] / row_3y_ago["adj_close"]) - 1
        if row_3y_ago["market_cap"]:
            result["market_cap_3y_ago"] = row_3y_ago["market_cap"]
            years_elapsed = (latest_date - row_3y_ago["trade_date"]).days / 365.25
            if years_elapsed > 0 and row_3y_ago["market_cap"] > 0:
                result["market_cap_cagr_3y"] = (
                    (latest["market_cap"] / row_3y_ago["market_cap"]) ** (1 / years_elapsed) - 1
                )

    return result


def main():
    prices = pd.read_csv(PRICES_CSV, parse_dates=["trade_date"])
    if prices.empty:
        print(f"{PRICES_CSV} is empty -- run pull_stock_history.py first.")
        return

    rows = []
    for ticker, group in prices.groupby("ticker"):
        rows.append(compute_metrics_for_ticker(ticker, group))

    analytics = pd.DataFrame(rows)

    # Attach company context (name, industry, product) for readability/insights
    companies = pd.read_csv(COMPANIES_CSV)[
        ["Company Name", "Ticker", "Industry", "Product", "Valuation"]
    ].rename(columns={"Company Name": "company_name", "Ticker": "ticker",
                       "Industry": "industry", "Product": "product",
                       "Valuation": "last_known_valuation"})
    analytics = companies.merge(analytics, on="ticker", how="inner")  # inner: only companies we computed data for

    analytics = analytics.sort_values("current_market_cap", ascending=False)
    analytics.to_csv(OUTPUT_CSV, index=False)

    n_3y = analytics["has_3y_history"].sum()
    print(f"Wrote {len(analytics)} companies to {OUTPUT_CSV}")
    print(f"  - {len(analytics)} have 1-year TSR computed")
    print(f"  - {n_3y} have full 3-year TSR / market cap CAGR computed")
    print(f"  - {len(analytics) - n_3y} have <3 years of history (recent IPOs) -- "
          f"3y fields will be blank for these")


if __name__ == "__main__":
    main()