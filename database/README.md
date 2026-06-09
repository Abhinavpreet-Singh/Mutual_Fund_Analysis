# 🗄️ Database Directory

This directory contains the relational SQLite database that acts as the data warehouse for the platform.

## 📄 File Details

- **`bluestock_mf.db`**: Relational database containing the populated data model.

## 📐 Data Model Schema
The database uses a Star Schema designed to support analytical queries and dashboard connections:

### Dimensions
1. **`dim_fund`**: Scheme master data (AMFI code, fund house, variant type, sebi category, expense ratio).
2. **`dim_date`**: Calendar date dimension (year, quarter, month, month name, weekend flags).

### Fact Tables
1. **`fact_nav`**: Daily historical NAV records and returns per scheme.
2. **`fact_aum`**: Quarterly AMC-level AUM details.
3. **`fact_monthly_sip`**: Industry monthly SIP inflows and active accounts.
4. **`fact_category_inflows`**: Sector/category-level monthly inflows.
5. **`fact_folio_count`**: Monthly active folio tallies.
6. **`fact_performance`**: Performance metrics (CAGR, Sharpe, Sortino, Alpha, Beta, Max Drawdown).
7. **`fact_transactions`**: Simulated transaction ledger.
8. **`fact_holdings`**: Security weights and sector allocations.
9. **`fact_benchmark`**: Daily index values for benchmark indices.

## ⚙️ Regeneration
To rebuild the schema and reload the database, run:
```bash
python run_pipeline.py
```
This triggers `scripts/etl_pipeline.py` which drops existing tables, creates the schema from the SQL file, and repopulates the tables from the processed CSV datasets.
