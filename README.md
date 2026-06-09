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
│   │   └── live_nav_*.csv      # Fetched from mfapi.in
│   └── processed/              # Cleaned & transformed data
├── database/                   # SQLite Database storage
│   └── bluestock_mf.db
├── notebooks/
│   ├── day1_eda_fund_master.ipynb
│   ├── EDA_Analysis.ipynb
│   ├── Performance_Analytics.ipynb
│   └── Advanced_Analytics.ipynb # Day 6 Advanced Risk and Cohort Analytics
├── scripts/                    # Consolidated Python data scripts (Day 7)
│   ├── etl_pipeline.py         # Consolidated ETL (Ingestion, Cleaning, SQLite build)
│   ├── live_nav_fetch.py       # Live NAV API fetcher from mfapi.in
│   ├── compute_metrics.py      # Day 4 & Day 6 Metrics computations
│   ├── recommender.py          # Fund Recommender Engine logic
│   └── day3_eda.py             # Day 3 EDA Visualizations module
├── sql/                        # SQL schema & queries (Day 2)
├── dashboard/                  # Power BI / HTML dashboard (Day 5)
├── reports/                    # Generated charts & text reports
│   ├── day3_charts/
│   ├── day4/                   # Day 4 Fund Performance Analytics reports & charts
│   └── day6/                   # Day 6 Advanced Analytics reports & charts
├── run_pipeline.py             # Day 7: Master execution script for the entire platform
├── recommender.py              # Day 7: Root CLI stub launcher for recommender
├── day3_eda.py                 # Day 7: Root stub redirecting imports for notebooks
├── data_dictionary.md          # Day 2: Column-level data dictionary
├── var_cvar_report.csv         # Day 6: Fund Value-at-Risk outputs (root copy)
├── rolling_sharpe_chart.png    # Day 6: Volatility of Sharpe ratios plot (root copy)
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
# 2. Enter workspace
cd Mutual_Fund_Analysis

# 3. Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 4. Run the master analytics pipeline
# This will clean data, rebuild SQLite DB, run SQL queries, plot charts, and calculate metrics.
python run_pipeline.py

# Optional: Run the pipeline while pulling fresh live NAV data from mfapi.in first
python run_pipeline.py --fetch-live

# 5. Run the fund recommender CLI
python recommender.py Moderate

# 6. Run the interactive Streamlit Web App locally
streamlit run dashboard/app.py
```

## 🌐 Public Cloud Deployment (Streamlit Community Cloud)

You can deploy this dashboard for free to share it publicly:
1. **Push the repository** to your personal GitHub account.
2. **Sign in** to [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account.
3. Click **"New App"** in the top right.
4. Select your **Repository**, **Branch** (`main`), and set the main file path to: `dashboard/app.py`.
5. Click **"Deploy"**. The cloud platform will read the project's `requirements.txt` to automatically install the dependencies and serve the interactive web app at a public shareable URL.


## ✅ Outputs Generated by the Pipeline

* **Data Cleaning Logs**: [`reports/data_cleaning_summary.txt`](file:///c:/repo/Mutual_Fund_Analysis/reports/data_cleaning_summary.txt)
* **Ingestion Report**: [`reports/data_ingestion_summary.txt`](file:///c:/repo/Mutual_Fund_Analysis/reports/data_ingestion_summary.txt)
* **SQLite Database**: [`database/bluestock_mf.db`](file:///c:/repo/Mutual_Fund_Analysis/database/bluestock_mf.db)
* **SQL Query Results**: [`reports/day2_query_results.md`](file:///c:/repo/Mutual_Fund_Analysis/reports/day2_query_results.md)
* **EDA Visualizations**: [`reports/day3_charts/`](file:///c:/repo/Mutual_Fund_Analysis/reports/day3_charts/) (16+ PNG/HTML plots)
* **Fund Performance Scorecard**: [`reports/day4/fund_scorecard.csv`](file:///c:/repo/Mutual_Fund_Analysis/reports/day4/fund_scorecard.csv)
* **VaR & CVaR Tail-Risk Report**: [`var_cvar_report.csv`](file:///c:/repo/Mutual_Fund_Analysis/var_cvar_report.csv)
* **Rolling Sharpe Ratio Plot**: [`rolling_sharpe_chart.png`](file:///c:/repo/Mutual_Fund_Analysis/rolling_sharpe_chart.png)
* **Sector HHI Concentration Risk**: [`reports/day6/sector_hhi.csv`](file:///c:/repo/Mutual_Fund_Analysis/reports/day6/sector_hhi.csv) and chart [`reports/day6/sector_hhi_chart.png`](file:///c:/repo/Mutual_Fund_Analysis/reports/day6/sector_hhi_chart.png)
* **SIP Churn Risk Flagging**: [`reports/day6/sip_continuity.csv`](file:///c:/repo/Mutual_Fund_Analysis/reports/day6/sip_continuity.csv)
* **Cohort Clustering Table**: [`reports/day6/cohort_analysis.csv`](file:///c:/repo/Mutual_Fund_Analysis/reports/day6/cohort_analysis.csv)
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
| **Day 7** | Final Report + Presentation + Deploy | ✅ Complete    |

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
