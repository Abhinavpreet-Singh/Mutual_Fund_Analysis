# Data Dictionary

## Source Files
- `data/raw/01_fund_master.csv`
- `data/raw/02_nav_history.csv`
- `data/raw/03_aum_by_fund_house.csv`
- `data/raw/04_monthly_sip_inflows.csv`
- `data/raw/05_category_inflows.csv`
- `data/raw/06_industry_folio_count.csv`
- `data/raw/07_scheme_performance.csv`
- `data/raw/08_investor_transactions.csv`
- `data/raw/09_portfolio_holdings.csv`
- `data/raw/10_benchmark_indices.csv`

## 1. `dim_fund`
Primary fund master dimension loaded from `01_fund_master.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `amfi_code` | INTEGER | raw | Primary key |
| `fund_house` | TEXT | raw | Fund house name |
| `scheme_name` | TEXT | raw | Scheme display name |
| `category` | TEXT | raw | Equity, Debt, Hybrid, etc. |
| `sub_category` | TEXT | raw | Large Cap, Gilt, Liquid, etc. |
| `plan` | TEXT | raw | Regular or Direct |
| `launch_date` | DATE | raw | Scheme launch date |
| `benchmark` | TEXT | raw | Benchmark index name |
| `expense_ratio_pct` | REAL | raw | Expense ratio in percent |
| `exit_load_pct` | REAL | raw | Exit load in percent |
| `min_sip_amount` | INTEGER | raw | Minimum SIP amount |
| `min_lumpsum_amount` | INTEGER | raw | Minimum lump sum amount |
| `fund_manager` | TEXT | raw | Fund manager name |
| `risk_category` | TEXT | raw | SEBI risk label |
| `sebi_category_code` | TEXT | raw | SEBI scheme code |

## 2. `fact_nav`
Daily NAV history loaded from `02_nav_history.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `amfi_code` | INTEGER | raw | Foreign key to `dim_fund` |
| `nav_date` | DATE | raw | NAV date |
| `nav` | REAL | raw | Cleaned NAV value |
| `daily_return` | REAL | derived | Computed with `pct_change()` within each scheme |

## 3. `fact_aum`
AUM by fund house loaded from `03_aum_by_fund_house.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `as_of_date` | DATE | raw | Reporting date |
| `fund_house` | TEXT | raw | Fund house name |
| `aum_lakh_crore` | REAL | raw | AUM in lakh crore |
| `aum_crore` | INTEGER | raw | AUM in crore |
| `num_schemes` | INTEGER | raw | Number of schemes |

## 4. `fact_monthly_sip`
Monthly SIP inflows loaded from `04_monthly_sip_inflows.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `month` | DATE | raw | Month start date |
| `sip_inflow_crore` | INTEGER | raw | SIP inflow in crore |
| `active_sip_accounts_crore` | REAL | raw | Active SIP accounts |
| `new_sip_accounts_lakh` | REAL | raw | New SIP registrations in lakh |
| `sip_aum_lakh_crore` | REAL | raw | SIP AUM in lakh crore |
| `yoy_growth_pct` | REAL | raw | Year-over-year growth percent |

## 5. `fact_category_inflows`
Category-level inflows loaded from `05_category_inflows.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `month` | DATE | raw | Month start date |
| `category` | TEXT | raw | Category label |
| `net_inflow_crore` | REAL | raw | Net inflow in crore |

## 6. `fact_folio_count`
Industry folio counts loaded from `06_industry_folio_count.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `month` | DATE | raw | Month start date |
| `total_folios_crore` | REAL | raw | Total folios |
| `equity_folios_crore` | REAL | raw | Equity folios |
| `debt_folios_crore` | REAL | raw | Debt folios |
| `hybrid_folios_crore` | REAL | raw | Hybrid folios |
| `others_folios_crore` | REAL | raw | Other folios |

## 7. `fact_performance`
Scheme performance snapshot loaded from `07_scheme_performance.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `amfi_code` | INTEGER | raw | Primary key |
| `scheme_name` | TEXT | raw | Scheme display name |
| `fund_house` | TEXT | raw | Fund house name |
| `category` | TEXT | raw | Scheme category |
| `plan` | TEXT | raw | Regular or Direct |
| `return_1yr_pct` | REAL | raw | 1-year return |
| `return_3yr_pct` | REAL | raw | 3-year return |
| `return_5yr_pct` | REAL | raw | 5-year return |
| `benchmark_3yr_pct` | REAL | raw | 3-year benchmark return |
| `alpha` | REAL | raw | Alpha |
| `beta` | REAL | raw | Beta |
| `sharpe_ratio` | REAL | raw | Sharpe ratio |
| `sortino_ratio` | REAL | raw | Sortino ratio |
| `std_dev_ann_pct` | REAL | raw | Annualized standard deviation |
| `max_drawdown_pct` | REAL | raw | Maximum drawdown |
| `aum_crore` | INTEGER | raw | AUM in crore |
| `expense_ratio_pct` | REAL | raw | Expense ratio in percent |
| `morningstar_rating` | INTEGER | raw | Morningstar rating |
| `risk_grade` | TEXT | raw | Risk grade label |

## 8. `fact_transactions`
Investor transaction records loaded from `08_investor_transactions.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `transaction_id` | INTEGER | derived | Auto-increment SQLite surrogate key |
| `investor_id` | TEXT | raw | Investor identifier |
| `transaction_date` | DATE | raw | Transaction date |
| `amfi_code` | INTEGER | raw | Foreign key to `dim_fund` |
| `transaction_type` | TEXT | cleaned | SIP, Lumpsum, Redemption |
| `amount_inr` | REAL | raw | Transaction amount in INR |
| `state` | TEXT | raw | Investor state |
| `city` | TEXT | raw | Investor city |
| `city_tier` | TEXT | raw | T30 or B30 |
| `age_group` | TEXT | raw | Age band |
| `gender` | TEXT | raw | Gender |
| `annual_income_lakh` | REAL | raw | Annual income in lakh |
| `payment_mode` | TEXT | raw | UPI, Mandate, etc. |
| `kyc_status` | TEXT | cleaned | Verified or Pending |

## 9. `fact_holdings`
Portfolio holdings loaded from `09_portfolio_holdings.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `amfi_code` | INTEGER | raw | Foreign key to `dim_fund` |
| `stock_symbol` | TEXT | raw | Stock ticker |
| `stock_name` | TEXT | raw | Company name |
| `sector` | TEXT | raw | Sector label |
| `weight_pct` | REAL | raw | Portfolio weight |
| `market_value_cr` | REAL | raw | Market value in crore |
| `current_price_inr` | REAL | raw | Current price in INR |
| `portfolio_date` | DATE | raw | Portfolio snapshot date |

## 10. `fact_benchmark`
Benchmark index history loaded from `10_benchmark_indices.csv`.

| Column | Type | Source | Notes |
| --- | --- | --- | --- |
| `benchmark_date` | DATE | raw | Market date |
| `index_name` | TEXT | raw | Benchmark name |
| `close_value` | REAL | raw | Closing index value |

## Cleaned CSV Outputs
- `data/processed/clean_nav.csv`
- `data/processed/clean_transactions.csv`
- `data/processed/clean_performance.csv`

## SQLite Database
- `bluestock_mf.db`
- Created tables: `dim_fund`, `fact_nav`, `fact_aum`, `fact_monthly_sip`, `fact_category_inflows`, `fact_folio_count`, `fact_performance`, `fact_transactions`, `fact_holdings`, `fact_benchmark`
