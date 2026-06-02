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
from sqlalchemy import create_engine

import clean_data

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
REPORT_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "bluestock_mf.db"
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

TABLE_COLUMNS = {
    "dim_fund": [
        "amfi_code", "fund_house", "scheme_name", "category", "sub_category", "plan",
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
        "amfi_code", "scheme_name", "fund_house", "category", "plan", "return_1yr_pct",
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

QUERY_MARKER = re.compile(r"^--\s*Q(\d+)\s*:\s*(.+)$")


def run_cleaning() -> list[dict]:
    """Run the cleaning pipeline and return dataset summaries."""
    return clean_data.main()


def read_sql_statements(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in text.split(";") if stmt.strip()]
    return statements


def build_schema(engine) -> None:
    """Create the SQLite schema from schema.sql."""
    statements = read_sql_statements(SCHEMA_PATH)
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        for statement in statements:
            conn.exec_driver_sql(statement)


def load_table(engine, table_name: str, dataframe: pd.DataFrame) -> None:
    columns = TABLE_COLUMNS[table_name]
    dataframe.loc[:, columns].to_sql(table_name, engine, if_exists="append", index=False)


def load_cleaned_data(engine) -> list[dict]:
    """Load every cleaned dataset into SQLite and return per-table row counts."""
    load_summary = []

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
        load_summary.append({
            "table": spec["table"],
            "rows": len(dataframe),
            "source": processed_path.name,
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


def run_queries(engine) -> str:
    """Execute the 10 SQL analytics queries and write a markdown report."""
    query_blocks = parse_queries(QUERIES_PATH)
    report_lines = ["# Day 2 Query Results", ""]

    with engine.connect() as conn:
        for block in query_blocks:
            df = pd.read_sql_query(block["sql"], conn)
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
    lines.append("")
    lines.append("## Loaded Tables")
    lines.append("")
    for item in load_summaries:
        lines.append(f"- {item['table']}: {item['rows']:,} rows from `{item['source']}`")
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

    print("Executing analytics queries …")
    query_report = run_queries(engine)

    build_summary(cleaning_summaries, load_summaries, query_report)

    print("\n[✓] SQLite database built →", DB_PATH)
    print("[✓] Query results saved →", QUERY_REPORT_PATH)
    print("[✓] Summary saved →", SUMMARY_PATH)


if __name__ == "__main__":
    main()
