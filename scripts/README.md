# 📜 Scripts Directory

This directory contains the Python modules and scripts that execute the data pipeline and recommendation workflows for the Mutual Fund Analytics Platform.

## 📄 File Details

1. **`live_nav_fetch.py`**: Fetches live NAV records from the `mfapi.in` API for designated schemes and writes raw CSVs to `data/raw/`. Includes network retries and error handling.
2. **`etl_pipeline.py`**: The core ETL controller. Ingests raw data, performs validation, standardizes column formats, drops duplicates, builds the SQLite database schema, loads the processed datasets, and executes analytical queries.
3. **`day3_eda.py`**: Generates and saves all 16+ Matplotlib and Plotly figures for exploratory analysis.
4. **`compute_metrics.py`**: Calculates all Day 4 performance metrics (CAGR, Sharpe, Sortino, Alpha, Beta, Drawdowns, Scorecard, and Tracking Error) and Day 6 risk metrics (Value at Risk, Conditional VaR, rolling Sharpe ratio, cohort analysis, investor churn risk, and sector HHI concentration). Updates the database and outputs files to `reports/`.
5. **`recommender.py`**: Queries the SQLite database to suggest the top 3 mutual funds matching a user's risk profile.

## ⚙️ Running Scripts
While scripts can be run individually (e.g., `python scripts/etl_pipeline.py`), it is recommended to execute the master run script from the root directory:
```bash
python run_pipeline.py
```
To run recommendations from the command line, use the root stub:
```bash
python recommender.py [Low/Moderate/High]
```
