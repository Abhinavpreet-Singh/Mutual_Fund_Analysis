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

## Loaded Tables

- dim_fund: 40 rows from `01_fund_master.csv`
- fact_nav: 46,000 rows from `clean_nav.csv`
- fact_aum: 90 rows from `03_aum_by_fund_house.csv`
- fact_monthly_sip: 48 rows from `04_monthly_sip_inflows.csv`
- fact_category_inflows: 144 rows from `05_category_inflows.csv`
- fact_folio_count: 21 rows from `06_industry_folio_count.csv`
- fact_performance: 40 rows from `clean_performance.csv`
- fact_transactions: 32,778 rows from `clean_transactions.csv`
- fact_holdings: 322 rows from `09_portfolio_holdings.csv`
- fact_benchmark: 8,050 rows from `10_benchmark_indices.csv`

Query results report: `C:\repo\Mutual_Fund_Analysis\reports\day2_query_results.md`