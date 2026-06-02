"""
clean_data.py
=============
Day 2 | Task 1-3
Cleans the raw CSV datasets and writes processed copies to data/processed/.

Dataset-specific rules:
- NAV history: parse dates, sort by AMFI code + date, forward-fill missing NAV,
  remove duplicates, validate NAV > 0
- Investor transactions: standardize transaction_type, validate amount > 0,
  normalize KYC values, parse transaction_date
- Scheme performance: coerce numeric fields, flag negative Sharpe ratios,
  check expense ratio range
- Other datasets: strip whitespace, parse date columns, drop duplicates, sort
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

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

SPECIAL_OUTPUTS = {
    "02_nav_history": "clean_nav.csv",
    "08_investor_transactions": "clean_transactions.csv",
    "07_scheme_performance": "clean_performance.csv",
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


def read_source_dataframe(key: str, filename: str) -> pd.DataFrame:
    """Read a source CSV and parse any known date columns."""
    read_kwargs = {"dtype": None}
    if key in {"01_fund_master", "02_nav_history", "07_scheme_performance", "08_investor_transactions", "09_portfolio_holdings", "10_benchmark_indices"}:
        read_kwargs["low_memory"] = False
    df = pd.read_csv(RAW_DIR / filename, **read_kwargs)
    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from object columns while preserving missing values."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    return df


def normalize_date_columns(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Parse known date/month columns for each dataset."""
    for col in DATE_COLS.get(key, []):
        if col not in df.columns:
            continue
        if col == "month":
            df[col] = pd.to_datetime(df[col], format="%Y-%m", errors="coerce")
        else:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def clean_nav_history(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = normalize_date_columns(df, "02_nav_history")
    df = clean_text_columns(df)
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    invalid_nav_before = int(df["nav"].le(0).fillna(False).sum())
    df.loc[df["nav"].le(0), "nav"] = np.nan

    before_rows = len(df)
    df = df.sort_values(["amfi_code", "date"], kind="stable")
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    duplicates_removed = before_rows - len(df)

    missing_before_fill = int(df["nav"].isna().sum())
    df["nav"] = df.groupby("amfi_code", sort=False)["nav"].transform(lambda s: s.ffill().bfill())
    missing_after_fill = int(df["nav"].isna().sum())

    df = df[df["nav"].gt(0)].copy()
    df = df.sort_values(["amfi_code", "date"], kind="stable").reset_index(drop=True)

    summary = {
        "notes": f"invalid NAV rows before fix: {invalid_nav_before}; missing NAV before fill: {missing_before_fill}; missing after fill: {missing_after_fill}",
        "duplicates_removed": duplicates_removed,
        "rows_removed": before_rows - len(df),
    }
    return df, summary


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = normalize_date_columns(df, "08_investor_transactions")
    df = clean_text_columns(df)

    transaction_map = {
        "sip": "SIP",
        "lumpsum": "Lumpsum",
        "lump sum": "Lumpsum",
        "redemption": "Redemption",
    }
    df["transaction_type"] = (
        df["transaction_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(transaction_map)
        .fillna(df["transaction_type"].astype(str).str.strip().str.title())
    )

    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    invalid_amounts = int(df["amount_inr"].isna().sum() + df["amount_inr"].le(0).fillna(False).sum())
    df = df[df["amount_inr"].gt(0)].copy()

    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    allowed_kyc = {"Verified", "Pending"}
    invalid_kyc = sorted(set(df.loc[~df["kyc_status"].isin(allowed_kyc), "kyc_status"].dropna().unique()))

    before_rows = len(df)
    df = df.sort_values(["transaction_date", "investor_id"], kind="stable")
    df = df.drop_duplicates().reset_index(drop=True)

    summary = {
        "notes": f"invalid amount rows removed: {invalid_amounts}; unexpected KYC values: {', '.join(invalid_kyc) if invalid_kyc else 'none'}",
        "duplicates_removed": before_rows - len(df),
        "rows_removed": invalid_amounts + (before_rows - len(df)),
    }
    return df, summary


def clean_performance(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = clean_text_columns(df)

    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
        "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
        "max_drawdown_pct", "aum_crore", "expense_ratio_pct", "morningstar_rating",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    negative_sharpe = int(df["sharpe_ratio"].lt(0).fillna(False).sum())
    expense_out_of_range = int((~df["expense_ratio_pct"].between(0.1, 2.5)).fillna(False).sum())

    before_rows = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "plan"], keep="last").reset_index(drop=True)

    summary = {
        "notes": f"negative Sharpe rows: {negative_sharpe}; expense ratio out of range: {expense_out_of_range}",
        "duplicates_removed": before_rows - len(df),
        "rows_removed": before_rows - len(df),
    }
    return df, summary


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
    df = read_source_dataframe(key, filename)
    before_rows = len(df)
    before_cols = df.shape[1]

    if key == "02_nav_history":
        df, extras = clean_nav_history(df)
    elif key == "08_investor_transactions":
        df, extras = clean_transactions(df)
    elif key == "07_scheme_performance":
        df, extras = clean_performance(df)
    else:
        df = clean_text_columns(df)
        df = normalize_date_columns(df, key)
        df = df.drop_duplicates().reset_index(drop=True)
        df = sort_if_possible(df, key)
        extras = {"notes": "standard cleanup only", "duplicates_removed": before_rows - len(df), "rows_removed": before_rows - len(df)}

    out_path = PROCESSED_DIR / filename
    df.to_csv(out_path, index=False)

    alias_path = SPECIAL_OUTPUTS.get(key)
    if alias_path:
        df.to_csv(PROCESSED_DIR / alias_path, index=False)

    summary = {
        "dataset": key,
        "input_rows": before_rows,
        "input_cols": before_cols,
        "output_rows": len(df),
        "output_cols": df.shape[1],
        "duplicates_removed": extras.get("duplicates_removed", 0),
        "rows_removed": extras.get("rows_removed", 0),
        "notes": extras.get("notes", ""),
        "output_path": out_path,
        "alias_path": alias_path,
    }
    return df, summary


def main() -> list[dict]:
    print(DIVIDER)
    print("BLUESTOCK FINTECH — DATA CLEANING")
    print("Day 2 | Tasks 1-3")
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
        if summary.get("notes"):
            report_lines.append(f"  -> {summary['notes']}")
    report_lines.append("")
    report_lines.append(f"Processed files written to: {PROCESSED_DIR}")

    report_path = REPORT_DIR / "data_cleaning_summary.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[✓] Cleaning report saved → {report_path}")
    return summaries


if __name__ == "__main__":
    main()
