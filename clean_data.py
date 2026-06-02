"""
clean_data.py
=============
Day 1 | Task 4
Cleans the raw CSV datasets and writes processed copies to data/processed/.

The cleaning rules are intentionally lightweight:
- strip whitespace from text columns
- parse known date/month columns
- drop duplicate rows
- sort by the primary date column when one exists
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "01_fund_master": "01_fund_master.csv",
    "02_nav_history": "02_nav_history.csv",
    "03_aum_by_fund_house": "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "05_category_inflows": "05_category_inflows.csv",
    "06_industry_folio_count": "06_industry_folio_count.csv",
    "07_scheme_performance": "07_scheme_performance.csv",
    "08_investor_transactions": "08_investor_transactions.csv",
    "09_portfolio_holdings": "09_portfolio_holdings.csv",
    "10_benchmark_indices": "10_benchmark_indices.csv",
}

DATE_COLS = {
    "01_fund_master": ["launch_date"],
    "02_nav_history": ["date"],
    "03_aum_by_fund_house": ["date"],
    "04_monthly_sip_inflows": ["month"],
    "05_category_inflows": ["month"],
    "06_industry_folio_count": ["month"],
    "07_scheme_performance": [],
    "08_investor_transactions": ["transaction_date"],
    "09_portfolio_holdings": ["portfolio_date"],
    "10_benchmark_indices": ["date"],
}

DIVIDER = "=" * 72


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from object columns while preserving missing values."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    return df


def parse_known_dates(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Parse the date columns that are present in each raw dataset."""
    for col in DATE_COLS.get(key, []):
        if col not in df.columns:
            continue
        if col == "month":
            df[col] = pd.to_datetime(df[col], format="%Y-%m", errors="coerce")
        else:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def sort_if_possible(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Sort on the primary date column if available."""
    preferred_order = ["date", "month", "transaction_date", "launch_date", "portfolio_date"]
    for col in preferred_order:
        if col in df.columns:
            return df.sort_values(col, kind="stable").reset_index(drop=True)
    return df.reset_index(drop=True)


def clean_dataset(key: str, filename: str) -> tuple[pd.DataFrame, dict]:
    raw_path = RAW_DIR / filename
    df = pd.read_csv(raw_path)
    before_rows = len(df)
    before_cols = df.shape[1]

    df = clean_text_columns(df)
    df = parse_known_dates(df, key)
    df = df.drop_duplicates().reset_index(drop=True)
    after_dedup_rows = len(df)
    df = sort_if_possible(df, key)

    out_path = PROCESSED_DIR / filename
    df.to_csv(out_path, index=False)

    summary = {
        "dataset": key,
        "input_rows": before_rows,
        "input_cols": before_cols,
        "output_rows": len(df),
        "output_cols": df.shape[1],
        "duplicates_removed": before_rows - after_dedup_rows,
        "output_path": out_path,
    }
    return df, summary


def main() -> list[dict]:
    print(DIVIDER)
    print("BLUESTOCK FINTECH — DATA CLEANING")
    print("Day 1 | Task 4")
    print(DIVIDER)

    summaries = []
    for key, filename in DATASETS.items():
        df, summary = clean_dataset(key, filename)
        summaries.append(summary)
        print(
            f"{key:<28} {summary['input_rows']:>8,} -> {summary['output_rows']:>8,} rows  "
            f"| saved {summary['output_path'].name}"
        )

    report_lines = [DIVIDER, "DATA CLEANING SUMMARY", DIVIDER]
    report_lines.append(f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append(f"{'Dataset':<28} {'Input':>10} {'Output':>10} {'Dupes':>8}")
    report_lines.append(f"{'-' * 28} {'-' * 10} {'-' * 10} {'-' * 8}")
    for summary in summaries:
        report_lines.append(
            f"{summary['dataset']:<28} {summary['input_rows']:>10,} {summary['output_rows']:>10,} {summary['duplicates_removed']:>8,}"
        )
    report_lines.append("")
    report_lines.append(f"Processed files written to: {PROCESSED_DIR}")

    report_path = REPORT_DIR / "data_cleaning_summary.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[✓] Cleaning report saved → {report_path}")
    return summaries


if __name__ == "__main__":
    main()
