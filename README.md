# 📈 Mutual Fund Analytics Platform

### Bluestock Fintech Capstone Project — Individual | 7-Day Sprint

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.2-green?logo=pandas)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![Status](https://img.shields.io/badge/Day-6%20Complete-brightgreen)

---

## 🎯 Project Overview

An end-to-end **Mutual Fund Analytics Platform** that ingests publicly available
data from AMFI India and mfapi.in, transforms it through a robust ETL pipeline,
stores it in a relational SQLite database, and presents insights via an
interactive dashboard.

**Data Source:** AMFI India (Public), [mfapi.in](https://api.mfapi.in), NSE/BSE
Public Data  
**Duration:** 7 Working Days | ~50–55 Hours  
**Technologies:** Python · SQL · Power BI/Tableau · Pandas · Matplotlib · Plotly

---

## 📁 Project Structure

```
Mutual_Fund_Analysis/
├── data/
│   ├── raw/                    # Source CSVs + live NAV fetches
│   │   ├── 01_fund_master.csv
│   │   ├── 02_nav_history.csv
│   │   ├── 03_aum_by_fund_house.csv
│   │   ├── 04_monthly_sip_inflows.csv
│   │   ├── 05_category_inflows.csv
│   │   ├── 06_industry_folio_count.csv
│   │   ├── 07_scheme_performance.csv
│   │   ├── 08_investor_transactions.csv
│   │   ├── 09_portfolio_holdings.csv
│   │   ├── 10_benchmark_indices.csv
│   │   └── live_nav_*.csv      # Fetched from mfapi.in
│   └── processed/              # Cleaned & transformed data
├── database/                   # SQLite Database storage
│   └── bluestock_mf.db
├── notebooks/
│   ├── day1_eda_fund_master.ipynb
│   ├── EDA_Analysis.ipynb
│   ├── Performance_Analytics.ipynb
│   └── Advanced_Analytics.ipynb # Day 6 Advanced Risk and Cohort Analytics
├── sql/                        # SQL schema & queries (Day 2)
├── dashboard/                  # Power BI / HTML dashboard (Day 5)
├── reports/                    # Generated charts & text reports
│   ├── day3_charts/
│   ├── day4/                   # Day 4 Fund Performance Analytics reports & charts
│   └── day6/                   # Day 6 Advanced Analytics reports & charts
├── data_ingestion.py           # Task 3: Load all 10 CSVs
├── clean_data.py               # Day 2: Dataset-specific cleaning and validation
├── live_nav_fetch.py           # Tasks 4 & 5: Fetch live NAV from mfapi.in
├── build_day2_sqlite.py        # Day 2: Build SQLite DB and run queries
├── run_performance_analytics.py # Day 4: Performance analytics pipeline
├── run_advanced_analytics.py   # Day 6: Advanced analytics and risk metrics pipeline
├── recommender.py              # Day 6: CLI Fund Recommendation System
├── validate_amfi_codes.py      # Task 7: AMFI code validation
├── data_dictionary.md          # Day 2: Column-level data dictionary
├── var_cvar_report.csv         # Day 6: Fund Value-at-Risk outputs
├── rolling_sharpe_chart.png    # Day 6: Volatility of Sharpe ratios plot
├── requirements.txt
└── README.md
```

---

## 🗂️ Datasets

| #   | File                        | Description                                                     | Rows    |
| --- | --------------------------- | --------------------------------------------------------------- | ------- |
| 01  | `fund_master.csv`           | 40 real MF schemes — codes, fund house, category, expense ratio | 40      |
| 02  | `nav_history.csv`           | Daily NAV Jan 2022 – May 2026                                   | ~46,000 |
| 03  | `aum_by_fund_house.csv`     | Quarterly AUM for 10 fund houses                                | ~90     |
| 04  | `monthly_sip_inflows.csv`   | Month-wise SIP inflow, accounts, registrations                  | 48      |
| 05  | `category_inflows.csv`      | Net inflows by fund category FY24-25                            | ~144    |
| 06  | `industry_folio_count.csv`  | Total MF folios broken by type                                  | 21      |
| 07  | `scheme_performance.csv`    | 1/3/5yr returns, Sharpe, Sortino, Alpha, Beta                   | 40      |
| 08  | `investor_transactions.csv` | 32K+ simulated SIP/Lumpsum/Redemption txns                      | ~32,000 |
| 09  | `portfolio_holdings.csv`    | Top equity holdings per scheme                                  | ~320    |
| 10  | `benchmark_indices.csv`     | Daily Nifty 50/100, BSE SmallCap, CRISIL indices                | ~8,000  |

---

## 🚀 Getting Started

```bash
# 1. Clone the repository
git clone <repo-url>
cd Mutual_Fund_Analysis

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run data ingestion (Task 3)
python data_ingestion.py

# 4. Clean raw data into data/processed/ (Day 2 tasks 1-3)
python clean_data.py

# 5. Fetch live NAV data (Tasks 4 & 5)
python live_nav_fetch.py

# 6. Build the SQLite database and run SQL analytics
python build_day2_sqlite.py

# 7. Validate AMFI codes (Task 7)
python validate_amfi_codes.py

# 8. Open EDA notebook (Tasks 6 & 7)
jupyter notebook notebooks/day1_eda_fund_master.ipynb
```

## ✅ What To Check After Each Run

- `python data_ingestion.py` writes `reports/data_ingestion_summary.txt`.
- `python clean_data.py` writes cleaned CSV copies into `data/processed/`, the
  three task-specific aliases (`clean_nav.csv`, `clean_transactions.csv`,
  `clean_performance.csv`), and `reports/data_cleaning_summary.txt`.
- `python build_day2_sqlite.py` creates `database/bluestock_mf.db`, `sql/schema.sql`,
  `sql/queries.sql`, `reports/day2_query_results.md`, and
  `reports/day2_summary.md`.
- `python run_performance_analytics.py` calculates performance metrics and saves CSV files and charts in `reports/day4/`, updating `database/bluestock_mf.db`.
- `python run_advanced_analytics.py` calculates Advanced Analytics and Risk Metrics, generating reports in `reports/day6/`, plotting charts, and saving key deliverables to the root directory.
- `python recommender.py [Low/Moderate/High]` matches a user's risk appetite with the top 3 mutual funds ranked by Sharpe ratio.
- `python live_nav_fetch.py` writes the fetched NAV CSVs into `data/raw/`.
- `python validate_amfi_codes.py` writes `reports/data_quality_report.txt`.
- Open `notebooks/day1_eda_fund_master.ipynb` and run the cells top to bottom to
  inspect all 10 datasets, fund-master breakdowns, and AMFI validation.
- If you do not already have a virtual environment, create one first and then
  install `requirements.txt`.

> `sqlite3` is part of Python's standard library, so it does not need to be
> installed with `pip`.

---

## 📅 7-Day Task Progress

| Day       | Focus Area                           | Status         |
| --------- | ------------------------------------ | -------------- |
| **Day 1** | Project Setup + Data Ingestion (ETL) | ✅ Complete    |
| **Day 2** | Data Cleaning + SQL Database Design  | ✅ Complete |
| **Day 3** | Exploratory Data Analysis (EDA)      | ✅ Complete     |
| **Day 4** | Fund Performance Analytics           | ✅ Complete     |
| **Day 5** | Dashboard Development                | ✅ Complete     |
| **Day 6** | Advanced Analytics + Risk Metrics    | ✅ Complete    |
| **Day 7** | Final Report + Presentation          | 🔲 Pending     |

---

## 📊 Key Business Metrics (Real-World Data)

| Metric                  | Value               | Source            |
| ----------------------- | ------------------- | ----------------- |
| Industry AUM (Dec 2025) | ₹81 lakh crore      | AMFI              |
| SBI MF AUM              | ₹12.50 lakh crore   | AMFI Quarterly    |
| SIP Inflow (Dec 2025)   | ₹31,002 crore (ATH) | AMFI Monthly Note |
| Active SIP Accounts     | 9.35 crore          | AMFI              |
| Total MF Folios         | 26.12 crore         | AMFI              |

---

## 🏢 Company

**Bluestock Fintech Pvt. Ltd.** — Democratising investment analytics for retail
and institutional investors in India.

> ⚠️ _All data is sourced from publicly available AMFI India / mfapi.in. This
> project is for educational purposes only and does not constitute financial
> advice._
