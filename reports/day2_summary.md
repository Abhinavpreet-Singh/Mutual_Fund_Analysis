# Day 2 Summary

## Completed

- Cleaned all 10 raw datasets with dataset-specific validation rules.
- Built the SQLite schema and loaded all cleaned tables into `bluestock_mf.db`.
- Executed 10 analytics queries and saved the results report.

## Outputs

- `bluestock_mf.db`
- `sql/schema.sql`
- `sql/queries.sql`
- `reports/day2_query_results.md`
- `reports/data_cleaning_summary.txt`
- `data_dictionary.md`

## Loaded Tables

- dim_date: 1,340 rows from `derived` (verified)
- dim_fund: 40 rows from `01_fund_master.csv` (verified)
- fact_nav: 46,000 rows from `clean_nav.csv` (verified)
- fact_aum: 90 rows from `03_aum_by_fund_house.csv` (verified)
- fact_monthly_sip: 48 rows from `04_monthly_sip_inflows.csv` (verified)
- fact_category_inflows: 144 rows from `05_category_inflows.csv` (verified)
- fact_folio_count: 21 rows from `06_industry_folio_count.csv` (verified)
- fact_performance: 40 rows from `clean_performance.csv` (verified)
- fact_transactions: 32,778 rows from `clean_transactions.csv` (verified)
- fact_holdings: 322 rows from `09_portfolio_holdings.csv` (verified)
- fact_benchmark: 8,050 rows from `10_benchmark_indices.csv` (verified)

Query results report: `C:\repo\Mutual_Fund_Analysis\reports\day2_query_results.md`