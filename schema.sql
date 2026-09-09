-- ============================================================
-- SaaS Companies Analytics Project — Database Schema
-- Works in SQLite, and ports easily to Postgres/MySQL if you
-- move the project there later (just swap AUTOINCREMENT / TEXT
-- types as needed).
-- ============================================================

DROP TABLE IF EXISTS stock_analytics;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS company_investors;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    company_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name    TEXT NOT NULL UNIQUE,
    founded_year    INTEGER,
    hq              TEXT,
    industry        TEXT,      -- raw source value (85 distinct, mostly 1-2 companies each)
    industry_bucket TEXT,      -- 12 broader sector groupings, added by prepare_part2_data.py -- use this for GROUP BY
    total_funding   TEXT,      -- original string, e.g. "$1B" -- kept for display/reference
    arr             TEXT,
    valuation       TEXT,      -- original string; NOT parsed to numeric -- see prepare_part2_data.py note on why.
                                -- For public companies, use stock_analytics.current_market_cap instead.
    total_funding_usd REAL,    -- numeric USD, parsed by prepare_part2_data.py (Oracle's placeholder "$2K" nulled out)
    arr_usd            REAL,
    employees       TEXT,
    top_investors   TEXT,      -- original comma-separated string -- see company_investors for normalized form
    product         TEXT,
    g2_rating       REAL,
    ticker          TEXT,      -- NULL for private companies
    exchange        TEXT,      -- NASDAQ / NYSE / NULL
    status          TEXT CHECK (status IN ('Public','Private')),
    notes           TEXT
);

-- Part 2 prep output: one row per (company, investor) pair, normalized from
-- the comma-separated Top Investors column. Populated by prepare_part2_data.py.
CREATE TABLE company_investors (
    company_name    TEXT NOT NULL,
    investor_name   TEXT NOT NULL,
    PRIMARY KEY (company_name, investor_name)
);

CREATE TABLE stock_prices (
    price_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open            REAL,
    high            REAL,
    low             REAL,
    close           REAL,
    adj_close       REAL,
    volume          INTEGER,
    shares_outstanding INTEGER,   -- current snapshot, held constant across the series (see pull_stock_history.py note)
    market_cap      REAL,         -- close * shares_outstanding
    UNIQUE(ticker, trade_date)
);

-- Part 1 output: one row per public company with enough price history to
-- compute TSR / CAGR. Populated by calculate_tsr_market_cap.py.
CREATE TABLE stock_analytics (
    ticker              TEXT PRIMARY KEY,
    company_name        TEXT NOT NULL,
    industry            TEXT,
    product             TEXT,
    last_known_valuation TEXT,
    as_of_date          DATE,
    years_of_data       REAL,
    has_3y_history       INTEGER,   -- 0/1 boolean
    current_price        REAL,
    shares_outstanding   INTEGER,
    current_market_cap   REAL,
    tsr_1y                REAL,
    tsr_3y                REAL,
    market_cap_3y_ago     REAL,
    market_cap_cagr_3y    REAL
);

CREATE INDEX idx_stock_prices_ticker ON stock_prices(ticker);
CREATE INDEX idx_stock_prices_date ON stock_prices(trade_date);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_industry_bucket ON companies(industry_bucket);
CREATE INDEX idx_company_investors_investor ON company_investors(investor_name);