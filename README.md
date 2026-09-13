# Top 100 SaaS Companies — Stock Performance & Investor Insights System

## Project Intro / Objective

This project analyzes a dataset of the top 100 SaaS companies to help retail
investors understand stock performance, valuation trends, and where notable investors concentrate.

It's built in two parts. Part 1 (Python) pulls 3 years of daily stock price history for the 53
publicly traded companies in the dataset and calculates 1-year and 3-year total shareholder return, 
current market capitalization, and 3-year market cap growth, giving retail investors insights
into company performance over time. 
Part 2 (SQL) aggregates revenue, funding, and investor activity by industry buckets.

Discrepancies in the source data required outside research (e.g. ticker symbols
and public/private status had to be manually verified) Furthermore, the `Valuation` column 
contained stale data, which was resolved by calculating market capitalization from live stock price
and shares outstanding data in Part 1.

## Methodology

**Part 1: Stock Performance**

- **1-Year TSR** = (Adjusted Close Today ÷ Adjusted Close 1 Year Ago) − 1
- **3-Year TSR** = (Adjusted Close Today ÷ Adjusted Close 3 Years Ago) − 1
- **Market Cap** = Close Price × Shares Outstanding
- **3-Year Market Cap CAGR** = (Market Cap Today ÷ Market Cap 3 Years Ago)^(1/years elapsed) − 1

TSR is calculated from dividend/split-adjusted close prices, so it reflects true 
total shareholder return rather than raw price movement. 3-Year TSR was not calculated 
and left blank for companies with less than 3 years of trading history (recent IPOs).

**Part 2: Industry & Investor Analysis**

- Companies are grouped into 12 broad industry buckets (Cybersecurity &
  Identity, Data/Analytics/AI, Fintech & Payments, and so on), since the
  source data's industry labels were too fragmented (85 distinct values
  across 100 companies) for meaningful aggregation
- Each company's list of top investors is normalized into one row per
  company-investor pair, enabling investor-level analysis (e.g. which sectors a
  given investor concentrates in and investor prevalence across companies)
- **Market-Cap-to-ARR Multiple** = Current Market Cap ÷ Annual Recurring
  Revenue, combining Part 1's calculated market cap with Part 2's revenue
  data to show how each public company is priced relative to its revenue

## Tableau Dashboard (Planned)

--

## Technologies Used

- Python (pandas, yfinance)
- SQLite
- Tableau Public

## How to Use This Code

Run Order:
  1. `prepare_data.py` — cleans currency columns, buckets industries, and
   builds the investor table
  2. `pull_stock_history.py` — pulls 3 years of daily price history
  3. `calculate_tsr_market_cap.py` — computes TSR, market cap, and CAGR
  4. `load_to_sqlite.py` — loads everything into `saas_companies.db`
  5. `part2_analysis.py` — runs the Part 2 analysis queries

Steps 1, 3, 4, and 5 run fully offline; only step 2 needs an internet connection.

## Needs of This Project

- **Retail Investors** — wanting to inform investment decisions with TSR/market cap/revenue-multiple 
  comparisons across public SaaS companies and sector-level revenue, funding, and notable investor trends
- **Asset Managers** — needing a consolidated view of stock performance, valuation multiples, 
and investor concentration patterns across a SaaS peer set to inform sector allocation 