# Day 1 Summary

## Completed

- Created and validated the project folder structure.
- Installed the Python dependencies from `requirements.txt`.
- Loaded all 10 CSV datasets with Pandas in `data_ingestion.py`.
- Cleaned the raw CSV datasets and wrote processed copies to `data/processed/`
  with `clean_data.py`.
- Fetched live NAV data from `mfapi.in` for HDFC Top 100 and the 5 requested
  Bluechip schemes in `live_nav_fetch.py`.
- Explored `fund_master` in `notebooks/day1_eda_fund_master.ipynb`.
- Validated that every AMFI code in `fund_master` exists in `nav_history` with
  `validate_amfi_codes.py`.

## Generated Outputs

- `reports/data_ingestion_summary.txt`
- `reports/data_cleaning_summary.txt`
- `reports/data_quality_report.txt`
- `data/processed/01_fund_master.csv`
- `data/processed/02_nav_history.csv`
- `data/processed/03_aum_by_fund_house.csv`
- `data/processed/04_monthly_sip_inflows.csv`
- `data/processed/05_category_inflows.csv`
- `data/processed/06_industry_folio_count.csv`
- `data/processed/07_scheme_performance.csv`
- `data/processed/08_investor_transactions.csv`
- `data/processed/09_portfolio_holdings.csv`
- `data/processed/10_benchmark_indices.csv`
- `data/raw/live_nav_hdfc_top100_125497.csv`
- `data/raw/live_nav_sbi_bluechip_119551.csv`
- `data/raw/live_nav_icici_bluechip_120503.csv`
- `data/raw/live_nav_nippon_largecap_118632.csv`
- `data/raw/live_nav_axis_bluechip_119092.csv`
- `data/raw/live_nav_kotak_bluechip_120841.csv`

## How To Run

```powershell
cd C:\repo\Mutual_Fund_Analysis
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe data_ingestion.py
.\.venv\Scripts\python.exe clean_data.py
.\.venv\Scripts\python.exe live_nav_fetch.py
.\.venv\Scripts\python.exe validate_amfi_codes.py
jupyter notebook notebooks\day1_eda_fund_master.ipynb
```

## How To Check

- Confirm the console output shows shapes, dtypes, and head rows for all 10
  datasets.
- Confirm `data/processed/` contains cleaned copies of all 10 CSVs.
- Open `reports/data_ingestion_summary.txt` to review the ingestion log.
- Open `reports/data_cleaning_summary.txt` to review the processing log.
- Open `reports/data_quality_report.txt` to confirm AMFI validation passes.
- Verify the raw NAV CSVs exist in `data/raw/`.
- Run the notebook cells top to bottom to review the Day 1 EDA.
