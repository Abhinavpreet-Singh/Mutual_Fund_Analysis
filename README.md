# 📈 Mutual Fund Analytics Platform

### Bluestock Fintech Capstone Project — Individual | 7-Day Sprint

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.2-green?logo=pandas)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![Status](https://img.shields.io/badge/Day-1%20Complete-brightgreen)

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
├── notebooks/
│   └── day1_eda_fund_master.ipynb
├── sql/                        # SQL schema & queries (Day 2)
├── dashboard/                  # Power BI / Tableau files (Day 5)
├── reports/                    # Generated charts & text reports
├── data_ingestion.py           # Task 3: Load all 10 CSVs
├── live_nav_fetch.py           # Tasks 4 & 5: Fetch live NAV from mfapi.in
├── validate_amfi_codes.py      # Task 7: AMFI code validation
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

# 4. Clean raw data into data/processed/ (Task 4)
python clean_data.py

# 5. Fetch live NAV data (Tasks 4 & 5)
python live_nav_fetch.py

# 6. Validate AMFI codes (Task 7)
python validate_amfi_codes.py

# 7. Open EDA notebook (Tasks 6 & 7)
jupyter notebook notebooks/day1_eda_fund_master.ipynb
```

## ✅ What To Check After Each Run

- `python data_ingestion.py` writes `reports/data_ingestion_summary.txt`.
- `python clean_data.py` writes cleaned CSV copies into `data/processed/` and
  `reports/data_cleaning_summary.txt`.
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

| Day       | Focus Area                           | Status      |
| --------- | ------------------------------------ | ----------- |
| **Day 1** | Project Setup + Data Ingestion (ETL) | ✅ Complete |
| **Day 2** | Data Cleaning + SQL Database Design  | 🔲 Pending  |
| **Day 3** | Exploratory Data Analysis (EDA)      | 🔲 Pending  |
| **Day 4** | Fund Performance Analytics           | 🔲 Pending  |
| **Day 5** | Dashboard Development                | 🔲 Pending  |
| **Day 6** | Advanced Analytics + Risk Metrics    | 🔲 Pending  |
| **Day 7** | Final Report + Presentation          | 🔲 Pending  |

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
