"""
Part 2: Product/Industry Group Metrics & Investor Prevalence

Same pattern as portfolio_optimization.py's SQL usage: write each query as a
plain string, run it with pd.read_sql(), get a DataFrame back.

Uses saas_companies.db (built by load_to_sqlite.py). Run this AFTER
load_to_sqlite.py has loaded the data -- these queries read from the
database, they don't load anything.

Usage:
    python part2_analysis.py
"""
import sqlite3
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

DB_PATH = "saas_companies.db"
conn = sqlite3.connect(DB_PATH)


# ------------------------------------------------------------
# Q1. Revenue (ARR) by industry bucket, highest first
# ------------------------------------------------------------
q1_arr_by_industry = """
SELECT
    industry_bucket,
    COUNT(*)                     AS company_count,
    SUM(arr_usd)                 AS total_arr_usd,
    ROUND(AVG(arr_usd), 0)       AS avg_arr_usd,
    ROUND(SUM(arr_usd) / 1e9, 2) AS total_arr_billions
FROM companies
WHERE arr_usd IS NOT NULL
GROUP BY industry_bucket
ORDER BY total_arr_usd DESC;
"""

# ------------------------------------------------------------
# Q2. Revenue (ARR) by product bundle, highest first
# (Product is per-company free text, not a shared category)
# ------------------------------------------------------------
q2_arr_by_product = """
SELECT
    product,
    COUNT(*)                     AS company_count,
    SUM(arr_usd)                 AS total_arr_usd,
    ROUND(SUM(arr_usd) / 1e9, 2) AS total_arr_billions
FROM companies
WHERE arr_usd IS NOT NULL
GROUP BY product
ORDER BY total_arr_usd DESC;
"""

# ------------------------------------------------------------
# Q3. Total funding raised by industry bucket, highest first
# (Oracle's placeholder "$2K" funding value was nulled out in prep)
# ------------------------------------------------------------
q3_funding_by_industry = """
SELECT
    industry_bucket,
    COUNT(*)                               AS company_count,
    SUM(total_funding_usd)                 AS total_funding_usd,
    ROUND(SUM(total_funding_usd) / 1e9, 2) AS total_funding_billions
FROM companies
WHERE total_funding_usd IS NOT NULL
GROUP BY industry_bucket
ORDER BY total_funding_usd DESC;
"""

# ------------------------------------------------------------
# Q4. Current market cap by industry bucket (public companies only) --
# uses Part 1's calculated market cap, not the static Valuation column
# ------------------------------------------------------------
q4_market_cap_by_industry = """
SELECT
    c.industry_bucket,
    COUNT(*)                                    AS public_company_count,
    SUM(sa.current_market_cap)                  AS total_market_cap_usd,
    ROUND(SUM(sa.current_market_cap) / 1e9, 2)  AS total_market_cap_billions,
    ROUND(AVG(sa.current_market_cap) / 1e9, 2)  AS avg_market_cap_billions
FROM companies c
JOIN stock_analytics sa ON sa.ticker = c.ticker
GROUP BY c.industry_bucket
ORDER BY total_market_cap_usd DESC;
"""

# ------------------------------------------------------------
# Q5. Market-cap-to-ARR multiple by company, public companies only
# ------------------------------------------------------------
q5_market_cap_to_arr = """
SELECT
    c.company_name,
    c.industry_bucket,
    c.arr_usd,
    sa.current_market_cap,
    ROUND(sa.current_market_cap / NULLIF(c.arr_usd, 0), 1) AS market_cap_to_arr_multiple
FROM companies c
JOIN stock_analytics sa ON sa.ticker = c.ticker
WHERE c.arr_usd IS NOT NULL
ORDER BY market_cap_to_arr_multiple DESC;
"""

# ------------------------------------------------------------
# Q6. Investor prevalence: which investors show up in the most
# portfolio companies overall
# ------------------------------------------------------------
q6_top_investors = """
SELECT
    investor_name,
    COUNT(*) AS portfolio_company_count
FROM company_investors
GROUP BY investor_name
ORDER BY portfolio_company_count DESC
LIMIT 20;
"""

# ------------------------------------------------------------
# Q7. Investor prevalence by industry bucket: for each sector, which
# investors appear more than once
# ------------------------------------------------------------
q7_investors_by_industry = """
SELECT
    c.industry_bucket,
    ci.investor_name,
    COUNT(*) AS companies_backed_in_bucket
FROM company_investors ci
JOIN companies c ON c.company_name = ci.company_name
GROUP BY c.industry_bucket, ci.investor_name
HAVING COUNT(*) > 1
ORDER BY companies_backed_in_bucket DESC, c.industry_bucket;
"""

# ------------------------------------------------------------
# Q8. For a specific investor, which sectors do they concentrate in?
# Swap INVESTOR_OF_INTEREST below to look at a different investor.
# ------------------------------------------------------------
INVESTOR_OF_INTEREST = "Sequoia"
q8_investor_sector_focus = """
SELECT
    ci.investor_name,
    c.industry_bucket,
    COUNT(*)                            AS company_count,
    GROUP_CONCAT(c.company_name, ', ')  AS companies
FROM company_investors ci
JOIN companies c ON c.company_name = ci.company_name
WHERE ci.investor_name = ?
GROUP BY ci.investor_name, c.industry_bucket
ORDER BY company_count DESC;
"""

# ------------------------------------------------------------
# Q9. Average ARR of companies each investor has backed
# ------------------------------------------------------------
q9_investor_avg_arr = """
SELECT
    ci.investor_name,
    COUNT(*)                       AS portfolio_company_count,
    ROUND(AVG(c.arr_usd) / 1e9, 2) AS avg_portfolio_arr_billions
FROM company_investors ci
JOIN companies c ON c.company_name = ci.company_name
WHERE c.arr_usd IS NOT NULL
GROUP BY ci.investor_name
HAVING COUNT(*) >= 3
ORDER BY avg_portfolio_arr_billions DESC;
"""

# ------------------------------------------------------------
# Q10. Public vs. private: ARR comparison
# ------------------------------------------------------------
q10_public_vs_private = """
SELECT
    status,
    COUNT(*)                     AS company_count,
    ROUND(AVG(arr_usd) / 1e9, 2) AS avg_arr_billions
FROM companies
WHERE arr_usd IS NOT NULL
GROUP BY status;
"""


def main():
    print("=== Q1: ARR by industry bucket ===")
    print(pd.read_sql(q1_arr_by_industry, conn))

    print("\n=== Q2: ARR by product bundle (top 10) ===")
    print(pd.read_sql(q2_arr_by_product, conn).head(10))

    print("\n=== Q3: Total funding by industry bucket ===")
    print(pd.read_sql(q3_funding_by_industry, conn))

    print("\n=== Q4: Market cap by industry bucket (public companies) ===")
    print(pd.read_sql(q4_market_cap_by_industry, conn))

    print("\n=== Q5: Market-cap-to-ARR multiple (top 10) ===")
    print(pd.read_sql(q5_market_cap_to_arr, conn).head(10))

    print("\n=== Q6: Top 20 investors by portfolio company count ===")
    print(pd.read_sql(q6_top_investors, conn))

    print("\n=== Q7: Investor prevalence by industry bucket ===")
    print(pd.read_sql(q7_investors_by_industry, conn))

    print(f"\n=== Q8: {INVESTOR_OF_INTEREST}'s sector focus ===")
    print(pd.read_sql(q8_investor_sector_focus, conn, params=(INVESTOR_OF_INTEREST,)))

    print("\n=== Q9: Average portfolio ARR by investor (top 10) ===")
    print(pd.read_sql(q9_investor_avg_arr, conn).head(10))

    print("\n=== Q10: Public vs. private ARR comparison ===")
    print(pd.read_sql(q10_public_vs_private, conn))


if __name__ == "__main__":
    main()