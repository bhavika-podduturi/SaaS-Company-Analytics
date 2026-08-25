"""
Part 1a: Import stock price and shares outstanding data over 3 years 
for each public company in the Top 100 SaaS Companies dataset.
"""

import pandas as pd
import yfinance as yf
import time

COMPANIES_CSV = "saas_companies_enriched.csv"
PRICES_CSV = "stock_prices.csv"
SHARES_CSV = "shares_outstanding.csv" 
PERIOD = "3y"          # 3 years of stock price history
INTERVAL = "1d"        # daily stock prices

# Note: for market cap, yfinance only gives a current value for shares outstanding
# So market_cap here = daily close price x TODAY's shares outstanding, held constant across the 3-year window. 
# This is a good approximation for large, stable-share-count companies, but it will
# understate/overstate history for companies with heavy buybacks, secondary
# offerings, or stock-based comp dilution during the window

# A few tickers changed during the lookback window. If a pull
# comes back empty, try the alternate symbol listed here.
TICKER_ALIASES = {
    "GTM": ["GTM", "ZI"],     # ZoomInfo: ZI -> GTM (2025)
    "XYZ": ["XYZ", "SQ"],     # Block: SQ -> XYZ (2025)
}

# Some formerly-public companies were taken private or acquired during the
# past 3 years (Splunk, HashiCorp, Vimeo, etc.). Their tickers are delisted,
# so Yahoo Finance will return no data for them

def fetch_shares_outstanding(ticker: str) -> dict:
    symbols_to_try = TICKER_ALIASES.get(ticker, [ticker])
    for sym in symbols_to_try:
        try:
            info = yf.Ticker(sym).info
        except Exception as e:
            print(f"    {sym}: error fetching info ({e})")
            continue
        shares = info.get("sharesOutstanding")
        if shares:
            return {"ticker": ticker, "shares_outstanding": shares, "source_symbol": sym}
    return {"ticker": ticker, "shares_outstanding": None, "source_symbol": None}


def fetch_one(ticker: str) -> pd.DataFrame:
    symbols_to_try = TICKER_ALIASES.get(ticker, [ticker])
    for sym in symbols_to_try:
        try:
            hist = yf.Ticker(sym).history(period=PERIOD, interval=INTERVAL, auto_adjust=False)
        except Exception as e:
            print(f"  {sym}: error ({e})")
            continue
        if not hist.empty:
            hist = hist.reset_index()
            hist["ticker"] = ticker  # keep the current ticker as the key
            return hist
    return pd.DataFrame()


def main():
    df = pd.read_csv(COMPANIES_CSV)
    public = df[df["Status"] == "Public"].dropna(subset=["Ticker"])
    tickers = sorted(public["Ticker"].unique().tolist())
    print(f"Pulling {PERIOD} of daily history for {len(tickers)} public companies...\n")

    all_rows = []
    shares_rows = []
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}")

        hist = fetch_one(ticker)
        if hist.empty:
            print(f"  -> no price data returned (may be too recently listed, or delisted)")
        else:
            all_rows.append(hist)

        shares_info = fetch_shares_outstanding(ticker)
        if shares_info["shares_outstanding"] is None:
            print(f"  -> no shares outstanding found")
        shares_rows.append(shares_info)

        time.sleep(0.3)  # be polite to the API

    # ---- shares outstanding table ----
    shares_df = pd.DataFrame(shares_rows)
    shares_df.to_csv(SHARES_CSV, index=False)
    print(f"\nWrote shares outstanding for {shares_df['shares_outstanding'].notna().sum()} "
          f"of {len(shares_df)} tickers to {SHARES_CSV}")

    if not all_rows:
        print("No price data pulled at all.")
        return

    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined.rename(columns={
        "Date": "trade_date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    combined["trade_date"] = pd.to_datetime(combined["trade_date"]).dt.date

    # Merge in shares outstanding and compute an approximate market cap series
    # (close price x current shares outstanding -- see note above).
    combined = combined.merge(
        shares_df[["ticker", "shares_outstanding"]], on="ticker", how="left"
    )
    combined["market_cap"] = combined["close"] * combined["shares_outstanding"]

    cols = ["ticker", "trade_date", "open", "high", "low", "close", "adj_close",
            "volume", "shares_outstanding", "market_cap"]
    combined = combined[cols].sort_values(["ticker", "trade_date"])

    combined.to_csv(PRICES_CSV, index=False)
    print(f"Wrote {len(combined)} rows for {combined['ticker'].nunique()} tickers to {PRICES_CSV}")


if __name__ == "__main__":
    main()