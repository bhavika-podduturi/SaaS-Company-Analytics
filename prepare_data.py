"""
Data Preparation: Gets the raw dataset ready for SQL analysis, which is done in part 2.
"""
import pandas as pd
import re

INPUT_CSV = "saas_companies_enriched.csv"
COMPANIES_OUTPUT_CSV = "saas_companies_clean.csv"
INVESTORS_OUTPUT_CSV = "company_investors.csv"

# Normalize currency columns from strings to plain numeric USD columns (e.g. standardizes "$1B", "$65.4M", etc)
CURRENCY_PATTERN = re.compile(r"^\$([\d,.]+)\s*([KMBT])?")
SCALE = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "T": 1_000_000_000_000, None: 1}

# Bucket the 85 raw Industry values into 12 broader sector groups, 
# so industry-level SQL aggregates reflect meaningful groups rather than mostly single-company categories
INDUSTRY_BUCKETS = {
    # Cybersecurity & Identity
    "Cloud Security": "Cybersecurity & Identity", "Cybersecurity": "Cybersecurity & Identity",
    "Data Security": "Cybersecurity & Identity", "Developer Security": "Cybersecurity & Identity",
    "Endpoint Management": "Cybersecurity & Identity", "Identity": "Cybersecurity & Identity",
    "Identity Management": "Cybersecurity & Identity", "Privacy & Security": "Cybersecurity & Identity",
    "Physical Security": "Cybersecurity & Identity",
    # Data, Analytics & AI
    "Business Intelligence": "Data, Analytics & AI", "Data & AI": "Data, Analytics & AI",
    "Data Analytics": "Data, Analytics & AI", "Data Streaming": "Data, Analytics & AI",
    "Data Warehousing": "Data, Analytics & AI", "Database": "Data, Analytics & AI",
    "Database/Spreadsheet": "Data, Analytics & AI", "Search & Analytics": "Data, Analytics & AI",
    "Search & Discovery": "Data, Analytics & AI", "Process Mining": "Data, Analytics & AI",
    "Product Analytics": "Data, Analytics & AI",
    # Fintech & Payments
    "BNPL": "Fintech & Payments", "Card Issuing": "Fintech & Payments",
    "Corporate Cards": "Fintech & Payments", "Equity Management": "Fintech & Payments",
    "Expense Management": "Fintech & Payments", "Financial APIs": "Fintech & Payments",
    "Financial Operations": "Fintech & Payments", "Financial Software": "Fintech & Payments",
    "Payments": "Fintech & Payments", "Spend Management": "Fintech & Payments",
    "Travel & Expense": "Fintech & Payments",
    # Marketing, Sales & CX
    "CRM": "Marketing, Sales & CX", "Customer Data": "Marketing, Sales & CX",
    "Customer Engagement": "Marketing, Sales & CX", "Customer Messaging": "Marketing, Sales & CX",
    "Customer Service": "Marketing, Sales & CX", "Email Marketing": "Marketing, Sales & CX",
    "Marketing & Sales": "Marketing, Sales & CX", "Marketing Automation": "Marketing, Sales & CX",
    "Revenue Intelligence": "Marketing, Sales & CX", "Sales Engagement": "Marketing, Sales & CX",
    "Sales Intelligence": "Marketing, Sales & CX", "Contact Center": "Marketing, Sales & CX",
    "Experience Management": "Marketing, Sales & CX",
    # Collaboration & Productivity
    "Collaboration": "Collaboration & Productivity", "Collaboration Software": "Collaboration & Productivity",
    "Productivity": "Collaboration & Productivity", "Work Management": "Collaboration & Productivity",
    "Writing Assistant": "Collaboration & Productivity", "Digital Agreements": "Collaboration & Productivity",
    "Scheduling": "Collaboration & Productivity", "Cloud Storage": "Collaboration & Productivity",
    # Design & Creative
    "Design": "Design & Creative", "Creative Software": "Design & Creative",
    # Communications & Video
    "Communications": "Communications & Video", "Team Communication": "Communications & Video",
    "Video Communications": "Communications & Video", "Video Platform": "Communications & Video",
    "Email Delivery": "Communications & Video",
    # HR & People Ops
    "HR & Finance": "HR & People Ops", "HR & IT": "HR & People Ops", "HR & Payroll": "HR & People Ops",
    # DevOps & IT Operations
    "APM": "DevOps & IT Operations", "CI/CD": "DevOps & IT Operations", "DevOps": "DevOps & IT Operations",
    "IT Service Management": "DevOps & IT Operations", "Infrastructure": "DevOps & IT Operations",
    "Web Infrastructure": "DevOps & IT Operations", "RPA": "DevOps & IT Operations",
    "Feature Management": "DevOps & IT Operations", "Monitoring & Analytics": "DevOps & IT Operations",
    "Observability": "DevOps & IT Operations", "Log Management": "DevOps & IT Operations",
    "Incident Response": "DevOps & IT Operations",
    # E-commerce & Web
    "E-commerce": "E-commerce & Web", "Web Publishing": "E-commerce & Web", "Website Building": "E-commerce & Web",
    # Vertical & Industry-Specific SaaS
    "Construction": "Vertical & Industry-Specific SaaS", "Field Service": "Vertical & Industry-Specific SaaS",
    "Life Sciences": "Vertical & Industry-Specific SaaS", "Life Sciences R&D": "Vertical & Industry-Specific SaaS",
    "Restaurant Tech": "Vertical & Industry-Specific SaaS", "IoT": "Vertical & Industry-Specific SaaS",
    # Enterprise Software / ERP
    "Enterprise Software": "Enterprise Software / ERP", "Database & Enterprise": "Enterprise Software / ERP",
}

def parse_currency(value):
    """'$65.4M' -> 65_400_000.0. Returns None for missing/unparseable values."""
    if pd.isna(value):
        return None
    match = CURRENCY_PATTERN.match(str(value).strip())
    if not match:
        return None
    number_str, suffix = match.groups()
    number = float(number_str.replace(",", ""))
    return number * SCALE[suffix]


def main():
    df = pd.read_csv(INPUT_CSV)

    # 1. Parse currency columns aside from the Valuation column. 
    # A different approach is developed for calculating a company's valuation/market cap in Part 1.
    df["total_funding_usd"] = df["Total Funding"].apply(parse_currency)
    df["arr_usd"] = df["ARR"].apply(parse_currency)

    unparsed = df[df["Total Funding"].notna() & df["total_funding_usd"].isna()]
    if not unparsed.empty:
        print(f"WARNING: {len(unparsed)} Total Funding values didn't parse:")
        print(unparsed[["Company Name", "Total Funding"]])

    # Filtering out Oracle's funding figure. Oracle's Total Funding is $2K, 
    # which is a placeholder in the source data since the company IPO'd in 1986.
    oracle_mask = (df["Company Name"] == "Oracle") & (df["total_funding_usd"] < 1_000_000)
    if oracle_mask.any():
        df.loc[oracle_mask, "total_funding_usd"] = None
        print("Note: nulled out Oracle's Total Funding ('$2K') as a placeholder value.")

    # 2. Industry bucketing
    df["industry_bucket"] = df["Industry"].map(INDUSTRY_BUCKETS)
    unmapped = df[df["industry_bucket"].isna()]
    if not unmapped.empty:
        print(f"WARNING: {len(unmapped)} companies have an Industry value with no bucket mapping:")
        print(unmapped[["Company Name", "Industry"]])

    df.to_csv(COMPANIES_OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df)} companies with numeric columns to {COMPANIES_OUTPUT_CSV}")
    print(f"  - total_funding_usd populated for {df['total_funding_usd'].notna().sum()}/{len(df)}")
    print(f"  - arr_usd populated for {df['arr_usd'].notna().sum()}/{len(df)}")
    print(f"  - industry_bucket populated for {df['industry_bucket'].notna().sum()}/{len(df)} "
          f"({df['industry_bucket'].nunique()} buckets)")

    # 3. Splits the comma-separated Top Investors column into a 
    # normalized company_investors junction table (one row per company-investor pair), 
    # so SQL can GROUP BY investor cleanly.
    investor_rows = []
    for _, row in df.iterrows():
        if pd.isna(row["Top Investors"]):
            continue
        investors = [name.strip() for name in row["Top Investors"].split(",")]
        for investor in investors:
            if investor:
                investor_rows.append({
                    "company_name": row["Company Name"],
                    "investor_name": investor,
                })

    investors_df = pd.DataFrame(investor_rows).drop_duplicates()
    investors_df.to_csv(INVESTORS_OUTPUT_CSV, index=False)
    print(f"\nWrote {len(investors_df)} company-investor pairs "
          f"({investors_df['investor_name'].nunique()} unique investors) to {INVESTORS_OUTPUT_CSV}")


if __name__ == "__main__":
    main()