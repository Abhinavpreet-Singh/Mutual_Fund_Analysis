"""
data_ingestion.py
=================
Day 1 – Task 3 | Bluestock Fintech Mutual Fund Analytics Platform
------------------------------------------------------------------
Loads all 10 provided CSV datasets using Pandas.
Prints shape, dtypes, and head() for each dataset.
Saves a consolidated data-quality summary to reports/data_ingestion_summary.txt
"""

import os
import sys
import pandas as pd
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
RAW_DIR    = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Dataset Registry ─────────────────────────────────────────────────────────
DATASETS = {
    "01_fund_master":          "01_fund_master.csv",
    "02_nav_history":          "02_nav_history.csv",
    "03_aum_by_fund_house":    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows":  "04_monthly_sip_inflows.csv",
    "05_category_inflows":     "05_category_inflows.csv",
    "06_industry_folio_count": "06_industry_folio_count.csv",
    "07_scheme_performance":   "07_scheme_performance.csv",
    "08_investor_transactions":"08_investor_transactions.csv",
    "09_portfolio_holdings":   "09_portfolio_holdings.csv",
    "10_benchmark_indices":    "10_benchmark_indices.csv",
}

# ─── Known date columns per dataset ───────────────────────────────────────────
DATE_COLS = {
    "01_fund_master":          ["launch_date"],
    "02_nav_history":          ["date"],
    "03_aum_by_fund_house":    ["date"],
    "04_monthly_sip_inflows":  ["month"],
    "05_category_inflows":     ["month"],
    "06_industry_folio_count": ["month"],
    "07_scheme_performance":   [],
    "08_investor_transactions":["transaction_date"],
    "09_portfolio_holdings":   ["portfolio_date"],
    "10_benchmark_indices":    ["date"],
}

# ─── Helpers ──────────────────────────────────────────────────────────────────
DIVIDER = "=" * 70


def load_dataset(key: str, filename: str) -> pd.DataFrame:
    """Read a CSV, parse date columns, return DataFrame."""
    path = RAW_DIR / filename
    date_cols = DATE_COLS.get(key, [])
    df = pd.read_csv(path, parse_dates=date_cols)
    return df


def inspect_dataset(key: str, df: pd.DataFrame) -> str:
    """Return a formatted inspection string for a dataset."""
    lines = []
    lines.append(DIVIDER)
    lines.append(f"  DATASET : {key}")
    lines.append(DIVIDER)
    lines.append(f"  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    lines.append("")

    # dtypes
    lines.append("  Column Data Types:")
    for col, dtype in df.dtypes.items():
        null_pct = df[col].isna().mean() * 100
        lines.append(f"    {col:<35} {str(dtype):<15}  nulls: {null_pct:.1f}%")

    lines.append("")
    lines.append("  First 5 Rows:")
    lines.append(df.head().to_string(index=False))
    lines.append("")
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    report_lines = []
    report_lines.append("BLUESTOCK FINTECH — DATA INGESTION REPORT")
    report_lines.append("Day 1 | Task 3 — All 10 CSV Datasets")
    report_lines.append(f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    loaded = {}

    for key, filename in DATASETS.items():
        filepath = RAW_DIR / filename
        if not filepath.exists():
            msg = f"[WARNING] File not found: {filepath}"
            print(msg)
            report_lines.append(msg)
            continue

        print(f"\nLoading  →  {filename} ...", end=" ", flush=True)
        df = load_dataset(key, filename)
        loaded[key] = df
        print(f"OK  ({df.shape[0]:,} rows × {df.shape[1]} cols)")

        inspection = inspect_dataset(key, df)
        print(inspection)
        report_lines.append(inspection)

    # ── Summary table ──────────────────────────────────────────────────────────
    summary_lines = [DIVIDER, "  SUMMARY — ALL DATASETS", DIVIDER]
    summary_lines.append(f"  {'Dataset':<35} {'Rows':>10} {'Cols':>6}")
    summary_lines.append(f"  {'-'*35} {'-'*10} {'-'*6}")
    total_rows = 0
    for key, df in loaded.items():
        summary_lines.append(f"  {key:<35} {df.shape[0]:>10,} {df.shape[1]:>6}")
        total_rows += df.shape[0]
    summary_lines.append(f"  {'TOTAL':<35} {total_rows:>10,}")
    summary_lines.append("")

    summary_text = "\n".join(summary_lines)
    print(summary_text)
    report_lines.append(summary_text)

    # ── Write report ───────────────────────────────────────────────────────────
    report_path = REPORT_DIR / "data_ingestion_summary.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n[✓] Report saved → {report_path}")

    return loaded


if __name__ == "__main__":
    dataframes = main()
