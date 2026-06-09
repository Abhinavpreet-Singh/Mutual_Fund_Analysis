# 📁 Data Directory

This directory contains the datasets for the Mutual Fund Analytics Platform, split into two stages: raw and processed.

## 🗂️ Structure

- **`raw/`**: Contains the source CSV files containing the original downloaded data, as well as live NAV files fetched from the `mfapi.in` API.
- **`processed/`**: Contains the cleaned, standardized, and validated CSV files produced by the ETL pipeline.

## 📄 File Details

### Raw Files (`data/raw/`)
1. `01_fund_master.csv`: Fund details for 40 mutual fund schemes.
2. `02_nav_history.csv`: Daily historical Net Asset Value (NAV) records from January 2022 to May 2026.
3. `03_aum_by_fund_house.csv`: Quarterly Assets Under Management (AUM) values for top AMCs.
4. `04_monthly_sip_inflows.csv`: Industry-wide monthly SIP inflows and active account counts.
5. `05_category_inflows.csv`: Inflows grouped by scheme category.
6. `06_industry_folio_count`: Number of active folios across scheme types.
7. `07_scheme_performance.csv`: Raw calculated performance statistics.
8. `08_investor_transactions.csv`: Transaction ledger containing ~32,000 transaction records.
9. `09_portfolio_holdings.csv`: Security weights and sector allocations for equity schemes.
10. `10_benchmark_indices.csv`: Daily close values for indices (Nifty 50, Nifty 100, etc.).

### Processed Files (`data/processed/`)
Cleaned and standard-validated versions of the raw datasets. Key aliases include:
- `clean_nav.csv`: Sorted, deduplicated NAV history with missing values forward-filled.
- `clean_transactions.csv`: Transaction ledger with standardized categories and validated amounts.
- `clean_performance.csv`: Numeric performance fields coerced, sorted, and deduplicated.
