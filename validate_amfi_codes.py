"""
validate_amfi_codes.py
======================
Day 1 – Task 7 | Bluestock Fintech Mutual Fund Analytics Platform
-----------------------------------------------------------------
Validates that every AMFI code in fund_master exists in nav_history.
Produces a plain-text data quality report saved to reports/data_quality_report.txt
"""

import pandas as pd
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
RAW_DIR    = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DIVIDER = "=" * 70
SEP     = "-" * 70


def load_data():
    fund_master = pd.read_csv(
        RAW_DIR / "01_fund_master.csv",
        parse_dates=["launch_date"],
    )
    nav_history = pd.read_csv(
        RAW_DIR / "02_nav_history.csv",
        parse_dates=["date"],
    )
    return fund_master, nav_history


def validate_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame) -> dict:
    """Core validation logic. Returns a dict of findings."""
    master_codes = set(fund_master["amfi_code"].unique())
    nav_codes    = set(nav_history["amfi_code"].unique())

    missing_in_nav    = master_codes - nav_codes   # in master but NOT in nav
    extra_in_nav      = nav_codes - master_codes   # in nav but NOT in master
    matched           = master_codes & nav_codes

    # Per-scheme NAV record counts
    nav_counts = nav_history.groupby("amfi_code").agg(
        nav_records=("nav", "count"),
        earliest_date=("date", "min"),
        latest_date=("date", "max"),
        min_nav=("nav", "min"),
        max_nav=("nav", "max"),
        null_nav=("nav", lambda x: x.isna().sum()),
    ).reset_index()

    merged = fund_master.merge(nav_counts, on="amfi_code", how="left")

    return {
        "master_codes":     master_codes,
        "nav_codes":        nav_codes,
        "matched":          matched,
        "missing_in_nav":   missing_in_nav,
        "extra_in_nav":     extra_in_nav,
        "nav_counts":       nav_counts,
        "merged":           merged,
    }


def build_report(fund_master: pd.DataFrame,
                 nav_history: pd.DataFrame,
                 v: dict) -> str:
    lines = []
    lines.append(DIVIDER)
    lines.append("  BLUESTOCK FINTECH — DATA QUALITY REPORT")
    lines.append("  Day 1 | Task 7 — AMFI Code Validation")
    lines.append(f"  Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(DIVIDER)

    # ── Overview ───────────────────────────────────────────────────────────────
    lines.append("\n[1] DATASET OVERVIEW")
    lines.append(SEP)
    lines.append(f"  fund_master  : {len(fund_master):>6,} rows  |  {fund_master['amfi_code'].nunique()} unique AMFI codes")
    lines.append(f"  nav_history  : {len(nav_history):>6,} rows  |  {nav_history['amfi_code'].nunique()} unique AMFI codes")
    lines.append(f"  NAV date range : {nav_history['date'].min().date()}  →  {nav_history['date'].max().date()}")

    # ── Code match summary ────────────────────────────────────────────────────
    lines.append("\n[2] AMFI CODE MATCH SUMMARY")
    lines.append(SEP)
    lines.append(f"  ✔  Codes in BOTH master & nav_history : {len(v['matched'])}")
    lines.append(f"  ✘  Codes in master  MISSING from nav  : {len(v['missing_in_nav'])}")
    lines.append(f"  ⚠  Codes in nav  NOT in master        : {len(v['extra_in_nav'])}")

    if v["missing_in_nav"]:
        lines.append("\n  Missing codes (in master, absent from nav_history):")
        missing_df = fund_master[fund_master["amfi_code"].isin(v["missing_in_nav"])][
            ["amfi_code", "scheme_name", "fund_house", "category"]
        ]
        lines.append(missing_df.to_string(index=False))
    else:
        lines.append("\n  ✔  All fund_master AMFI codes are present in nav_history.")

    if v["extra_in_nav"]:
        lines.append("\n  Extra codes (in nav_history, absent from fund_master):")
        for code in sorted(v["extra_in_nav"]):
            lines.append(f"    {code}")

    # ── Per-scheme NAV coverage ────────────────────────────────────────────────
    lines.append("\n[3] PER-SCHEME NAV COVERAGE")
    lines.append(SEP)
    display_cols = [
        "amfi_code", "scheme_name", "fund_house",
        "nav_records", "earliest_date", "latest_date",
        "min_nav", "max_nav", "null_nav",
    ]
    coverage = v["merged"][display_cols].copy()
    coverage["earliest_date"] = coverage["earliest_date"].dt.date
    coverage["latest_date"]   = coverage["latest_date"].dt.date
    lines.append(coverage.to_string(index=False))

    # ── NAV completeness ──────────────────────────────────────────────────────
    lines.append("\n[4] NAV COMPLETENESS STATS")
    lines.append(SEP)
    total_nav_rows   = len(nav_history)
    null_nav_rows    = nav_history["nav"].isna().sum()
    dup_rows         = nav_history.duplicated(subset=["amfi_code", "date"]).sum()
    lines.append(f"  Total NAV rows         : {total_nav_rows:,}")
    lines.append(f"  Null NAV values        : {null_nav_rows:,}  ({null_nav_rows/total_nav_rows*100:.2f}%)")
    lines.append(f"  Duplicate (code+date)  : {dup_rows:,}")

    # Avg records per scheme
    avg_recs = v["nav_counts"]["nav_records"].mean()
    min_recs = v["nav_counts"]["nav_records"].min()
    max_recs = v["nav_counts"]["nav_records"].max()
    lines.append(f"  Avg NAV records/scheme : {avg_recs:.0f}")
    lines.append(f"  Min NAV records/scheme : {min_recs}  (scheme: "
                 f"{v['nav_counts'].loc[v['nav_counts']['nav_records'].idxmin(), 'amfi_code']})")
    lines.append(f"  Max NAV records/scheme : {max_recs}  (scheme: "
                 f"{v['nav_counts'].loc[v['nav_counts']['nav_records'].idxmax(), 'amfi_code']})")

    # ── fund_master column checks ─────────────────────────────────────────────
    lines.append("\n[5] FUND MASTER — NULL CHECK")
    lines.append(SEP)
    for col in fund_master.columns:
        nulls = fund_master[col].isna().sum()
        status = "✔" if nulls == 0 else "✘"
        lines.append(f"  {status}  {col:<35}  nulls: {nulls}")

    # ── Verdict ───────────────────────────────────────────────────────────────
    lines.append("\n[6] OVERALL VERDICT")
    lines.append(SEP)
    issues = len(v["missing_in_nav"]) + null_nav_rows + dup_rows
    if issues == 0:
        lines.append("  ✔  DATA QUALITY: PASS — No critical issues found.")
    else:
        lines.append(f"  ⚠  DATA QUALITY: REVIEW NEEDED — {issues} issue(s) detected.")
    lines.append("")
    lines.append(DIVIDER)
    return "\n".join(lines)


def main():
    print("Loading datasets …")
    fund_master, nav_history = load_data()

    print("Running validation …")
    v = validate_codes(fund_master, nav_history)

    report_text = build_report(fund_master, nav_history, v)
    print(report_text)

    report_path = REPORT_DIR / "data_quality_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n[✓] Data quality report saved → {report_path}")


if __name__ == "__main__":
    main()
