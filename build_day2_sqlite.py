"""
build_day2_sqlite.py
====================
Day 2 | SQLite build and analytics runner

Workflow:
1. Run the Day 2 cleaning pipeline.
2. Build the SQLite schema from sql/schema.sql.
3. Load the cleaned datasets into bluestock_mf.db.
4. Execute the 10 analytics queries from sql/queries.sql.
5. Write a markdown results report and a short build summary.
"""

from __future__ import annotations

from pathlib import Path
import re
import sqlite3

import pandas as pd
from sqlalchemy import create_engine, text

import clean_data

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
REPORT_DIR = BASE_DIR / "reports"
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = SQL_DIR / "schema.sql"
QUERIES_PATH = SQL_DIR / "queries.sql"
QUERY_REPORT_PATH = REPORT_DIR / "day2_query_results.md"
SUMMARY_PATH = REPORT_DIR / "day2_summary.md"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
SQL_DIR.mkdir(parents=True, exist_ok=True)

TABLE_SPECS = [
    {
        "dataset": "01_fund_master",
        "file": "01_fund_master.csv",
        "table": "dim_fund",
        "parse_dates": ["launch_date"],
    },
    {
        "dataset": "02_nav_history",
        "file": "clean_nav.csv",
        "table": "fact_nav",
        "parse_dates": ["date"],
    },
    {
        "dataset": "03_aum_by_fund_house",
        "file": "03_aum_by_fund_house.csv",
        "table": "fact_aum",
        "parse_dates": ["date"],
    },
    {
        "dataset": "04_monthly_sip_inflows",
        "file": "04_monthly_sip_inflows.csv",
        "table": "fact_monthly_sip",
        "parse_dates": ["month"],
    },
    {
        "dataset": "05_category_inflows",
        "file": "05_category_inflows.csv",
        "table": "fact_category_inflows",
        "parse_dates": ["month"],
    },
    {
        "dataset": "06_industry_folio_count",
        "file": "06_industry_folio_count.csv",
        "table": "fact_folio_count",
        "parse_dates": ["month"],
    },
    {
        "dataset": "07_scheme_performance",
        "file": "clean_performance.csv",
        "table": "fact_performance",
        "parse_dates": [],
    },
    {
        "dataset": "08_investor_transactions",
        "file": "clean_transactions.csv",
        "table": "fact_transactions",
        "parse_dates": ["transaction_date"],
    },
    {
        "dataset": "09_portfolio_holdings",
        "file": "09_portfolio_holdings.csv",
        "table": "fact_holdings",
        "parse_dates": ["portfolio_date"],
    },
    {
        "dataset": "10_benchmark_indices",
        "file": "10_benchmark_indices.csv",
        "table": "fact_benchmark",
        "parse_dates": ["date"],
    },
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
    "dim_date": [
        "date_value", "year", "quarter", "month", "month_name",
        "day_of_month", "day_of_week", "day_name", "is_weekend",
    ],
    "dim_fund": [
        "amfi_code", "fund_house", "scheme_name", "category", "sub_category", "variant_type",
        "launch_date", "benchmark", "expense_ratio_pct", "exit_load_pct",
        "min_sip_amount", "min_lumpsum_amount", "fund_manager", "risk_category",
        "sebi_category_code",
    ],
    "fact_nav": ["amfi_code", "nav_date", "nav", "daily_return"],
    "fact_aum": ["as_of_date", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"],
    "fact_monthly_sip": [
        "month", "sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh",
        "sip_aum_lakh_crore", "yoy_growth_pct",
    ],
    "fact_category_inflows": ["month", "category", "net_inflow_crore"],
    "fact_folio_count": [
        "month", "total_folios_crore", "equity_folios_crore", "debt_folios_crore",
        "hybrid_folios_crore", "others_folios_crore",
    ],
    "fact_performance": [
        "amfi_code", "scheme_name", "fund_house", "category", "variant_type", "return_1yr_pct",
        "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct", "alpha", "beta",
        "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "expense_ratio_pct", "morningstar_rating", "risk_grade",
    ],
    "fact_transactions": [
        "investor_id", "transaction_date", "amfi_code", "transaction_type", "amount_inr",
        "state", "city", "city_tier", "age_group", "gender", "annual_income_lakh",
        "payment_mode", "kyc_status",
    ],
    "fact_holdings": [
        "amfi_code", "stock_symbol", "stock_name", "sector", "weight_pct",
        "market_value_cr", "current_price_inr", "portfolio_date",
    ],
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

QUERY_MARKER = re.compile(r"^--\s*Q(\d+)\s*:\s*(.+)$")
TOP_MARKER = re.compile(r"SELECT\s+TOP\s+(\d+)\s+", re.IGNORECASE)


SQLITE_SCHEMA = """
DROP TABLE IF EXISTS fact_benchmark;
DROP TABLE IF EXISTS fact_holdings;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_folio_count;
DROP TABLE IF EXISTS fact_category_inflows;
DROP TABLE IF EXISTS fact_monthly_sip;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

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


def run_cleaning() -> list[dict]:
    """Run the cleaning pipeline and return dataset summaries."""
    return clean_data.main()


def build_schema(engine) -> None:
    with engine.begin() as conn:
        raw_connection = conn.connection
        raw_connection.executescript("PRAGMA foreign_keys = ON;\n" + SQLITE_SCHEMA)


def build_date_dimension(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create the date dimension from all date-bearing source columns."""
    series_list = []
    for dataset, column in DATE_DIM_SOURCES:
        frame = dataframes[dataset]
        values = pd.to_datetime(frame[column], errors="coerce").dropna().dt.strftime("%Y-%m-%d")
        series_list.append(values)

    dates = pd.Index(pd.unique(pd.concat(series_list, ignore_index=True))).sort_values()
    date_frame = pd.DataFrame({"date_value": dates})
    parsed = pd.to_datetime(date_frame["date_value"], errors="coerce")
    date_frame["year"] = parsed.dt.year
    date_frame["quarter"] = parsed.dt.quarter
    date_frame["month"] = parsed.dt.month
    date_frame["month_name"] = parsed.dt.strftime("%b")
    date_frame["day_of_month"] = parsed.dt.day
    date_frame["day_of_week"] = parsed.dt.dayofweek + 1
    date_frame["day_name"] = parsed.dt.day_name()
    date_frame["is_weekend"] = (parsed.dt.dayofweek >= 5).astype(int)
    return date_frame


def load_table(engine, table_name: str, dataframe: pd.DataFrame) -> None:
    source_frame = dataframe.copy()
    if table_name in {"dim_fund", "fact_performance"} and "plan" in source_frame.columns:
        source_frame["variant_type"] = source_frame["plan"].values
    columns = TABLE_COLUMNS[table_name]
    table_frame = source_frame.loc[:, columns].copy()
    for column in TABLE_DATE_COLUMNS.get(table_name, []):
        table_frame[column] = pd.to_datetime(table_frame[column], errors="coerce").dt.strftime("%Y-%m-%d")
    table_frame.to_sql(table_name, engine, if_exists="append", index=False)


def load_cleaned_data(engine) -> list[dict]:
    """Load every cleaned dataset into SQLite and return per-table row counts."""
    load_summary = []
    source_frames: dict[str, pd.DataFrame] = {}

    for spec in TABLE_SPECS:
        processed_path = PROCESSED_DIR / spec["file"]
        dataframe = pd.read_csv(processed_path, parse_dates=spec["parse_dates"])
        source_frames[spec["dataset"]] = dataframe.copy()

    date_dimension = build_date_dimension(source_frames)
    load_table(engine, "dim_date", date_dimension)
    with engine.connect() as conn:
        db_count = int(conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar_one())
    load_summary.append({
        "table": "dim_date",
        "source_rows": len(date_dimension),
        "db_rows": db_count,
        "source": "derived",
        "verified": len(date_dimension) == db_count,
    })

    for spec in TABLE_SPECS:
        processed_path = PROCESSED_DIR / spec["file"]
        dataframe = pd.read_csv(processed_path, parse_dates=spec["parse_dates"])

        if spec["table"] == "fact_nav":
            dataframe = dataframe.sort_values(["amfi_code", "date"], kind="stable").reset_index(drop=True)
            dataframe["daily_return"] = dataframe.groupby("amfi_code", sort=False)["nav"].pct_change()
            dataframe = dataframe.rename(columns={"date": "nav_date"})
        elif spec["table"] == "fact_transactions":
            dataframe = dataframe.sort_values(["transaction_date", "investor_id"], kind="stable").reset_index(drop=True)
        elif spec["table"] == "fact_aum":
            dataframe = dataframe.rename(columns={"date": "as_of_date"})
        elif spec["table"] == "fact_performance":
            dataframe = dataframe.sort_values(["amfi_code", "plan"], kind="stable").reset_index(drop=True)
        elif spec["table"] == "fact_benchmark":
            dataframe = dataframe.rename(columns={"date": "benchmark_date"})

        load_table(engine, spec["table"], dataframe)
        with engine.connect() as conn:
            db_rows = conn.execute(text(f"SELECT COUNT(*) FROM {spec['table']}"))
            db_count = int(db_rows.scalar_one())
        load_summary.append({
            "table": spec["table"],
            "source_rows": len(dataframe),
            "db_rows": db_count,
            "source": processed_path.name,
            "verified": len(dataframe) == db_count,
        })

    return load_summary


def parse_queries(path: Path) -> list[dict]:
    """Parse labeled SQL blocks from queries.sql."""
    lines = path.read_text(encoding="utf-8").splitlines()
    queries = []
    current = None
    current_sql: list[str] = []

    for line in lines:
        match = QUERY_MARKER.match(line)
        if match:
            if current is not None:
                queries.append({"label": current[0], "title": current[1], "sql": "\n".join(current_sql).strip()})
            current = (match.group(1), match.group(2).strip())
            current_sql = []
            continue
        if current is not None:
            current_sql.append(line)

    if current is not None:
        queries.append({"label": current[0], "title": current[1], "sql": "\n".join(current_sql).strip()})

    return queries


def translate_query_to_sqlite(sql: str) -> str:
    """Translate the SQL Server flavored query file into SQLite-compatible SQL."""
    top_match = TOP_MARKER.search(sql)
    limit_value = None
    if top_match:
        limit_value = int(top_match.group(1))
        sql = TOP_MARKER.sub("SELECT ", sql, count=1)

    sql = sql.replace("CONVERT(char(7), nav_date, 120)", "substr(nav_date, 1, 7)")
    sql = sql.replace("CONVERT(char(4), month, 120)", "substr(month, 1, 4)")
    sql = sql.replace("LEFT(CONVERT(varchar(7), nav_date, 120), 7)", "substr(nav_date, 1, 7)")
    sql = sql.replace("LEFT(CONVERT(varchar(4), month, 120), 4)", "substr(month, 1, 4)")
    sql = sql.replace("CONVERT(varchar(7), nav_date, 120)", "substr(nav_date, 1, 7)")
    sql = sql.replace("CONVERT(varchar(4), month, 120)", "substr(month, 1, 4)")

    if limit_value is not None:
        sql = sql.rstrip(";") + f"\nLIMIT {limit_value};"
    return sql


def run_queries(engine) -> str:
    """Execute the 10 SQL analytics queries and write a markdown report."""
    query_blocks = parse_queries(QUERIES_PATH)
    report_lines = ["# Day 2 Query Results", ""]

    with engine.connect() as conn:
        for block in query_blocks:
            sql_text = translate_query_to_sqlite(block["sql"])
            df = pd.read_sql_query(sql_text, conn)
            report_lines.append(f"## Q{block['label']}: {block['title']}")
            report_lines.append("")
            report_lines.append(f"Rows returned: {len(df)}")
            report_lines.append("")
            report_lines.append(df.to_string(index=False))
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

    QUERY_REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    return str(QUERY_REPORT_PATH)


def build_summary(cleaning_summaries: list[dict], load_summaries: list[dict], query_report: str) -> None:
    lines = ["# Day 2 Summary", ""]
    lines.append("## Completed")
    lines.append("")
    lines.append("- Cleaned all 10 raw datasets with dataset-specific validation rules.")
    lines.append("- Built the SQLite schema and loaded all cleaned tables into `bluestock_mf.db`.")
    lines.append("- Executed 10 analytics queries and saved the results report.")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append("- `bluestock_mf.db`")
    lines.append("- `sql/schema.sql`")
    lines.append("- `sql/queries.sql`")
    lines.append("- `reports/day2_query_results.md`")
    lines.append("- `reports/data_cleaning_summary.txt`")
    lines.append("- `data_dictionary.md`")
    lines.append("")
    lines.append("## Loaded Tables")
    lines.append("")
    for item in load_summaries:
        status = "verified" if item["verified"] else "mismatch"
        lines.append(f"- {item['table']}: {item['db_rows']:,} rows from `{item['source']}` ({status})")
    lines.append("")
    lines.append(f"Query results report: `{query_report}`")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("=" * 72)
    print("BLUESTOCK FINTECH — DAY 2 SQLITE PIPELINE")
    print("=" * 72)

    print("Running cleaning pipeline …")
    cleaning_summaries = run_cleaning()

    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = create_engine(f"sqlite:///{DB_PATH.resolve().as_posix()}")
    print("Building schema …")
    build_schema(engine)

    print("Loading cleaned datasets into SQLite …")
    load_summaries = load_cleaned_data(engine)

    mismatches = [item for item in load_summaries if not item["verified"]]
    if mismatches:
        raise RuntimeError(f"Row count verification failed for: {', '.join(item['table'] for item in mismatches)}")

    print("Executing analytics queries …")
    query_report = run_queries(engine)

    build_summary(cleaning_summaries, load_summaries, query_report)

    print("\n[✓] SQLite database built →", DB_PATH)
    print("[✓] Query results saved →", QUERY_REPORT_PATH)
    print("[✓] Summary saved →", SUMMARY_PATH)


if __name__ == "__main__":
    main()
