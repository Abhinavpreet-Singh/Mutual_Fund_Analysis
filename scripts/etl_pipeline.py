"""
scripts/etl_pipeline.py
=======================
Consolidated ETL pipeline for the Bluestock Mutual Fund Analytics Platform.
This script:
1. Ingests all 10 raw datasets from data/raw/.
2. Cleans and standardizes datasets according to specific business rules.
3. Builds the SQLite database schema and populates tables.
4. Generates data-quality, cleaning, and SQLite query reports.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ─── Path Configuration ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
REPORT_DIR = BASE_DIR / "reports"
DB_DIR = BASE_DIR / "database"

# Ensure target directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = SQL_DIR / "schema.sql"
QUERIES_PATH = SQL_DIR / "queries.sql"

DIVIDER = "=" * 75

# ─── Dataset & Table Configuration ───────────────────────────────────────────
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

SPECIAL_OUTPUTS = {
    "02_nav_history": "clean_nav.csv",
    "08_investor_transactions": "clean_transactions.csv",
    "07_scheme_performance": "clean_performance.csv",
}

TABLE_SPECS = [
    {"dataset": "01_fund_master", "file": "01_fund_master.csv", "table": "dim_fund", "parse_dates": ["launch_date"]},
    {"dataset": "02_nav_history", "file": "clean_nav.csv", "table": "fact_nav", "parse_dates": ["date"]},
    {"dataset": "03_aum_by_fund_house", "file": "03_aum_by_fund_house.csv", "table": "fact_aum", "parse_dates": ["date"]},
    {"dataset": "04_monthly_sip_inflows", "file": "04_monthly_sip_inflows.csv", "table": "fact_monthly_sip", "parse_dates": ["month"]},
    {"dataset": "05_category_inflows", "file": "05_category_inflows.csv", "table": "fact_category_inflows", "parse_dates": ["month"]},
    {"dataset": "06_industry_folio_count", "file": "06_industry_folio_count.csv", "table": "fact_folio_count", "parse_dates": ["month"]},
    {"dataset": "07_scheme_performance", "file": "clean_performance.csv", "table": "fact_performance", "parse_dates": []},
    {"dataset": "08_investor_transactions", "file": "clean_transactions.csv", "table": "fact_transactions", "parse_dates": ["transaction_date"]},
    {"dataset": "09_portfolio_holdings", "file": "09_portfolio_holdings.csv", "table": "fact_holdings", "parse_dates": ["portfolio_date"]},
    {"dataset": "10_benchmark_indices", "file": "10_benchmark_indices.csv", "table": "fact_benchmark", "parse_dates": ["date"]},
]

DATE_DIM_SOURCES = [
    ("01_fund_master", "launch_date"),
    ("02_nav_history", "date"),
    ("03_aum_by_fund_house", "date"),
    ("04_monthly_sip_inflows", "month"),
    ("05_category_inflows", "month"),
    ("06_industry_folio_count", "month"),
    ("08_investor_transactions", "transaction_date"),
    ("09_portfolio_holdings", "portfolio_date"),
    ("10_benchmark_indices", "date"),
]

TABLE_COLUMNS = {
    "dim_date": ["date_value", "year", "quarter", "month", "month_name", "day_of_month", "day_of_week", "day_name", "is_weekend"],
    "dim_fund": ["amfi_code", "fund_house", "scheme_name", "category", "sub_category", "variant_type", "launch_date", "benchmark", "expense_ratio_pct", "exit_load_pct", "min_sip_amount", "min_lumpsum_amount", "fund_manager", "risk_category", "sebi_category_code"],
    "fact_nav": ["amfi_code", "nav_date", "nav", "daily_return"],
    "fact_aum": ["as_of_date", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"],
    "fact_monthly_sip": ["month", "sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct"],
    "fact_category_inflows": ["month", "category", "net_inflow_crore"],
    "fact_folio_count": ["month", "total_folios_crore", "equity_folios_crore", "debt_folios_crore", "hybrid_folios_crore", "others_folios_crore"],
    "fact_performance": ["amfi_code", "scheme_name", "fund_house", "category", "variant_type", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct", "morningstar_rating", "risk_grade"],
    "fact_transactions": ["investor_id", "transaction_date", "amfi_code", "transaction_type", "amount_inr", "state", "city", "city_tier", "age_group", "gender", "annual_income_lakh", "payment_mode", "kyc_status"],
    "fact_holdings": ["amfi_code", "stock_symbol", "stock_name", "sector", "weight_pct", "market_value_cr", "current_price_inr", "portfolio_date"],
    "fact_benchmark": ["benchmark_date", "index_name", "close_value"],
}

TABLE_DATE_COLUMNS = {
    "dim_date": ["date_value"],
    "dim_fund": ["launch_date"],
    "fact_nav": ["nav_date"],
    "fact_aum": ["as_of_date"],
    "fact_monthly_sip": ["month"],
    "fact_category_inflows": ["month"],
    "fact_folio_count": ["month"],
    "fact_transactions": ["transaction_date"],
    "fact_holdings": ["portfolio_date"],
    "fact_benchmark": ["benchmark_date"],
}

SQLITE_SCHEMA = """
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    variant_type TEXT NOT NULL,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date_value TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL
);

CREATE TABLE fact_nav (
    amfi_code INTEGER NOT NULL,
    nav_date TEXT NOT NULL,
    nav REAL NOT NULL,
    daily_return REAL,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (nav_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_aum (
    as_of_date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore INTEGER,
    num_schemes INTEGER,
    PRIMARY KEY (fund_house, as_of_date),
    FOREIGN KEY (as_of_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_monthly_sip (
    month TEXT PRIMARY KEY,
    sip_inflow_crore INTEGER,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL,
    FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_category_inflows (
    month TEXT NOT NULL,
    category TEXT NOT NULL,
    net_inflow_crore REAL,
    PRIMARY KEY (month, category),
    FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_folio_count (
    month TEXT PRIMARY KEY,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL,
    FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    variant_type TEXT NOT NULL,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore INTEGER,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_holdings (
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (portfolio_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_benchmark (
    benchmark_date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL,
    PRIMARY KEY (benchmark_date, index_name),
    FOREIGN KEY (benchmark_date) REFERENCES dim_date (date_value)
);
"""

QUERY_MARKER = re.compile(r"^--\s*Q(\d+)\s*:\s*(.+)$")
TOP_MARKER = re.compile(r"SELECT\s+TOP\s+(\d+)\s+", re.IGNORECASE)


# ─── Step 1: Ingest Data ──────────────────────────────────────────────────────
def run_ingestion() -> dict[str, pd.DataFrame]:
    """Load raw CSV files from data/raw/, run initial inspection, and save log."""
    print("\nExecuting Data Ingestion...")
    report_lines = [
        "BLUESTOCK FINTECH — DATA INGESTION SUMMARY REPORT",
        "Unified Pipeline ETL",
        f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    ]
    loaded = {}

    for key, filename in DATASETS.items():
        filepath = RAW_DIR / filename
        if not filepath.exists():
            msg = f"[WARNING] File not found: {filepath}"
            print(msg)
            report_lines.append(msg)
            continue

        date_cols = DATE_COLS.get(key, [])
        df = pd.read_csv(filepath, parse_dates=date_cols)
        loaded[key] = df
        print(f"  Ingested {filename:<28} | {df.shape[0]:>6,} rows x {df.shape[1]} columns")

        # Format inspection report
        report_lines.append(DIVIDER)
        report_lines.append(f"  DATASET : {key} ({filename})")
        report_lines.append(DIVIDER)
        report_lines.append(f"  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns\n")
        report_lines.append("  Column Data Types:")
        for col, dtype in df.dtypes.items():
            null_pct = df[col].isna().mean() * 100
            report_lines.append(f"    {col:<35} {str(dtype):<15}  nulls: {null_pct:.1f}%")
        report_lines.append("")

    report_path = REPORT_DIR / "data_ingestion_summary.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"[SUCCESS] Ingestion logs saved to {report_path}")
    return loaded


# ─── Step 2: Clean Data ───────────────────────────────────────────────────────
def clean_nav_history(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw NAV history dataset."""
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
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
        "notes": f"invalid NAV rows: {invalid_nav_before}; missing pre-fill: {missing_before_fill}; post-fill: {missing_after_fill}",
        "duplicates_removed": duplicates_removed,
        "rows_removed": before_rows - len(df),
    }
    return df, summary


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw transactions dataset."""
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    transaction_map = {"sip": "SIP", "lumpsum": "Lumpsum", "lump sum": "Lumpsum", "redemption": "Redemption"}
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
        "notes": f"invalid amount rows: {invalid_amounts}; invalid KYC: {', '.join(invalid_kyc) if invalid_kyc else 'none'}",
        "duplicates_removed": before_rows - len(df),
        "rows_removed": invalid_amounts + (before_rows - len(df)),
    }
    return df, summary


def clean_performance(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw performance metrics dataset."""
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
        "notes": f"negative Sharpe: {negative_sharpe}; expense ratio out of range: {expense_out_of_range}",
        "duplicates_removed": before_rows - len(df),
        "rows_removed": before_rows - len(df),
    }
    return df, summary


def clean_general(df: pd.DataFrame, key: str) -> tuple[pd.DataFrame, dict]:
    """Run generalized cleanup (whitespace stripping, simple date parsing, duplicate dropping)."""
    # Trim text
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
        
    # Standard date parser
    for col in DATE_COLS.get(key, []):
        if col in df.columns:
            if col == "month":
                df[col] = pd.to_datetime(df[col], format="%Y-%m", errors="coerce")
            else:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                
    before_rows = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    
    # Sort
    sort_cols = ["date", "month", "transaction_date", "launch_date", "portfolio_date"]
    for col in sort_cols:
        if col in df.columns:
            df = df.sort_values(col, kind="stable").reset_index(drop=True)
            break
            
    summary = {
        "notes": "standardized column trimming and sorting",
        "duplicates_removed": before_rows - len(df),
        "rows_removed": before_rows - len(df),
    }
    return df, summary


def run_cleaning(loaded_dfs: dict[str, pd.DataFrame]) -> list[dict]:
    """Clean all loaded dataframes, save results, and generate the report."""
    print("\nExecuting Data Cleaning...")
    summaries = []
    
    for key, df in loaded_dfs.items():
        filename = DATASETS[key]
        if key == "02_nav_history":
            clean_df, ext = clean_nav_history(df)
        elif key == "08_investor_transactions":
            clean_df, ext = clean_transactions(df)
        elif key == "07_scheme_performance":
            clean_df, ext = clean_performance(df)
        else:
            clean_df, ext = clean_general(df, key)
            
        out_path = PROCESSED_DIR / filename
        clean_df.to_csv(out_path, index=False)
        
        # Check for special alias exports
        alias = SPECIAL_OUTPUTS.get(key)
        if alias:
            clean_df.to_csv(PROCESSED_DIR / alias, index=False)
            
        summary = {
            "dataset": key,
            "input_rows": len(df),
            "output_rows": len(clean_df),
            "duplicates_removed": ext["duplicates_removed"],
            "notes": ext["notes"],
            "output_file": filename
        }
        summaries.append(summary)
        print(f"  Cleaned {filename:<28} | {len(df):>6,} -> {len(clean_df):>6,} rows | saved processed file")
        
    # Write report
    report_lines = [
        DIVIDER,
        "BLUESTOCK FINTECH — DATA CLEANING & STANDARDIZATION SUMMARY",
        DIVIDER,
        f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"{'Dataset':<28} {'Input':>10} {'Output':>10} {'Dupes':>8}",
        f"{'-'*28} {'-'*10} {'-'*10} {'-'*8}"
    ]
    for s in summaries:
        report_lines.append(f"{s['dataset']:<28} {s['input_rows']:>10,} {s['output_rows']:>10,} {s['duplicates_removed']:>8,}")
        if s["notes"]:
            report_lines.append(f"  ↳ Note: {s['notes']}")
            
    report_path = REPORT_DIR / "data_cleaning_summary.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[SUCCESS] Cleaning summary saved to {report_path}")
    return summaries


# ─── Step 3: Database Build ──────────────────────────────────────────────────
def build_date_dimension(engine) -> pd.DataFrame:
    """Consolidate dates across all source fields to build the Date dimension."""
    series_list = []
    for dataset, column in DATE_DIM_SOURCES:
        processed_file = DATASETS[dataset] if dataset not in SPECIAL_OUTPUTS else SPECIAL_OUTPUTS[dataset]
        filepath = PROCESSED_DIR / processed_file
        if not filepath.exists():
            continue
        frame = pd.read_csv(filepath)
        if column in frame.columns:
            vals = pd.to_datetime(frame[column], errors="coerce").dropna().dt.strftime("%Y-%m-%d")
            series_list.append(vals)
            
    dates = pd.Index(pd.unique(pd.concat(series_list, ignore_index=True))).sort_values()
    df = pd.DataFrame({"date_value": dates})
    parsed = pd.to_datetime(df["date_value"])
    df["year"] = parsed.dt.year
    df["quarter"] = parsed.dt.quarter
    df["month"] = parsed.dt.month
    df["month_name"] = parsed.dt.strftime("%b")
    df["day_of_month"] = parsed.dt.day
    df["day_of_week"] = parsed.dt.dayofweek + 1
    df["day_name"] = parsed.dt.day_name()
    df["is_weekend"] = (parsed.dt.dayofweek >= 5).astype(int)
    return df


def load_cleaned_tables(engine) -> list[dict]:
    """Load cleaned CSVs into the relational SQLite database."""
    load_summary = []
    
    # 1. Date Dimension
    date_df = build_date_dimension(engine)
    date_df.to_sql("dim_date", engine, if_exists="append", index=False)
    load_summary.append({"table": "dim_date", "rows": len(date_df)})
    
    # 2. Other Tables
    for spec in TABLE_SPECS:
        filepath = PROCESSED_DIR / spec["file"]
        df = pd.read_csv(filepath, parse_dates=spec["parse_dates"])
        table_name = spec["table"]
        
        # Field renaming / transformation adaptations
        if table_name in {"dim_fund", "fact_performance"} and "plan" in df.columns:
            df["variant_type"] = df["plan"].values
        elif table_name == "fact_nav":
            df = df.sort_values(["amfi_code", "date"], kind="stable").reset_index(drop=True)
            df["daily_return"] = df.groupby("amfi_code", sort=False)["nav"].pct_change()
            df = df.rename(columns={"date": "nav_date"})
        elif table_name == "fact_transactions":
            df = df.sort_values(["transaction_date", "investor_id"], kind="stable").reset_index(drop=True)
        elif table_name == "fact_aum":
            df = df.rename(columns={"date": "as_of_date"})
        elif table_name == "fact_benchmark":
            df = df.rename(columns={"date": "benchmark_date"})
            
        columns = TABLE_COLUMNS[table_name]
        table_df = df.loc[:, columns].copy()
        
        # Convert date columns back to clean string format for SQLite compatibility
        for col in TABLE_DATE_COLUMNS.get(table_name, []):
            if col in table_df.columns:
                table_df[col] = pd.to_datetime(table_df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                
        table_df.to_sql(table_name, engine, if_exists="append", index=False)
        load_summary.append({"table": table_name, "rows": len(table_df)})
        print(f"  Loaded {table_name:<25} | {len(table_df):>6,} rows successfully loaded")
        
    return load_summary


def build_sqlite_db() -> list[dict]:
    """Rebuild SQLite database from scratch, execute schema, and populate tables."""
    print("\nBuilding SQLite Database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SQLITE_SCHEMA)
    conn.close()
    
    engine = create_engine(f"sqlite:///{DB_PATH.resolve().as_posix()}")
    load_summary = load_cleaned_tables(engine)
    print(f"[SUCCESS] SQLite database rebuilt at {DB_PATH}")
    return load_summary


# ─── Step 4: Analytical Queries ───────────────────────────────────────────────
def translate_to_sqlite(sql: str) -> str:
    """Convert T-SQL features (TOP/CONVERT) to SQLite equivalents."""
    top_match = TOP_MARKER.search(sql)
    limit_val = None
    if top_match:
        limit_val = int(top_match.group(1))
        sql = TOP_MARKER.sub("SELECT ", sql, count=1)
        
    # Format dates
    sql = sql.replace("CONVERT(char(7), nav_date, 120)", "substr(nav_date, 1, 7)")
    sql = sql.replace("CONVERT(char(4), month, 120)", "substr(month, 1, 4)")
    sql = sql.replace("LEFT(CONVERT(varchar(7), nav_date, 120), 7)", "substr(nav_date, 1, 7)")
    sql = sql.replace("LEFT(CONVERT(varchar(4), month, 120), 4)", "substr(month, 1, 4)")
    sql = sql.replace("CONVERT(varchar(7), nav_date, 120)", "substr(nav_date, 1, 7)")
    sql = sql.replace("CONVERT(varchar(4), month, 120)", "substr(month, 1, 4)")
    
    if limit_val is not None:
        sql = sql.rstrip(";") + f"\nLIMIT {limit_val};"
    return sql


def run_analytical_queries():
    """Run the 10 analytical SQL queries on the populated SQLite database."""
    print("\nRunning Analytical Queries (Day 2 queries.sql)...")
    if not QUERIES_PATH.exists():
        print(f"  [WARNING] Analytical queries file not found at {QUERIES_PATH}")
        return
        
    queries = []
    lines = QUERIES_PATH.read_text(encoding="utf-8").splitlines()
    current_q = None
    current_sql = []
    
    for line in lines:
        match = QUERY_MARKER.match(line)
        if match:
            if current_q:
                queries.append({"label": current_q[0], "title": current_q[1], "sql": "\n".join(current_sql).strip()})
            current_q = (match.group(1), match.group(2).strip())
            current_sql = []
            continue
        if current_q:
            current_sql.append(line)
            
    if current_q:
        queries.append({"label": current_q[0], "title": current_q[1], "sql": "\n".join(current_sql).strip()})
        
    report_lines = ["# Day 2 Analytics Query Results (Re-run in Unified ETL)", ""]
    engine = create_engine(f"sqlite:///{DB_PATH.resolve().as_posix()}")
    
    with engine.connect() as conn:
        for q in queries:
            sql_text = translate_to_sqlite(q["sql"])
            try:
                df = pd.read_sql_query(sql_text, conn)
                report_lines.append(f"## Q{q['label']}: {q['title']}")
                report_lines.append("")
                report_lines.append(f"Rows returned: {len(df)}")
                report_lines.append("")
                report_lines.append(df.to_string(index=False))
                report_lines.append("\n" + "---" + "\n")
                print(f"  Ran Q{q['label']}: {q['title'][:40]}... | {len(df)} rows")
            except Exception as e:
                report_lines.append(f"## Q{q['label']}: {q['title']} - [ERROR]")
                report_lines.append(f"Query execution failed: {e}\n")
                print(f"  [ERROR] Q{q['label']} failed: {e}")
                
    report_path = REPORT_DIR / "day2_query_results.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[SUCCESS] Query results summary saved to {report_path}")


# ─── Master Pipeline Controller ───────────────────────────────────────────────
def main():
    print(DIVIDER)
    print("BLUESTOCK FINTECH — CONSOLIDATED ETL PIPELINE (Ingestion, Cleaning, DB)")
    print(DIVIDER)
    
    # 1. Load Data
    raw_dfs = run_ingestion()
    
    # 2. Clean Data
    run_cleaning(raw_dfs)
    
    # 3. Create SQLite Database
    db_load_summary = build_sqlite_db()
    
    # 4. Run Queries
    run_analytical_queries()
    
    print("\n[SUCCESS] ETL pipeline run completed successfully.")
    print(DIVIDER)


if __name__ == "__main__":
    main()
