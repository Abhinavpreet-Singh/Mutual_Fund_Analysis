"""
live_nav_fetch.py
=================
Day 1 – Tasks 4 & 5 | Bluestock Fintech Mutual Fund Analytics Platform
-----------------------------------------------------------------------
Task 4: Fetch live NAV from mfapi.in for HDFC Top 100 (code 125497).
Task 5: Fetch NAV for 5 Bluechip schemes and save raw CSV files.

Scheme codes:
  125497 – HDFC Top 100 Fund (Direct)
  119551 – SBI Bluechip Fund (Regular)
  120503 – ICICI Pru Bluechip Fund (Regular)
  118632 – Nippon India Large Cap Fund (Regular)
  119092 – Axis Bluechip Fund (Regular)
  120841 – Kotak Bluechip Fund (Regular)
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
RAW_DIR    = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_BASE   = "https://api.mfapi.in/mf"
TIMEOUT    = 30          # seconds per request
RETRY_WAIT = 3           # seconds between retries
MAX_RETRY  = 3

# ─── Scheme Registry ──────────────────────────────────────────────────────────
# Task 4 anchor scheme
HDFC_TOP100 = {
    "code": 125497,
    "name": "HDFC Top 100 Fund - Direct Plan - Growth",
    "file": "live_nav_hdfc_top100_125497.csv",
}

# Task 5 – 5 Bluechip schemes
BLUECHIP_SCHEMES = [
    {"code": 119551, "name": "SBI Bluechip Fund - Regular",           "file": "live_nav_sbi_bluechip_119551.csv"},
    {"code": 120503, "name": "ICICI Pru Bluechip Fund - Regular",     "file": "live_nav_icici_bluechip_120503.csv"},
    {"code": 118632, "name": "Nippon India Large Cap Fund - Regular",  "file": "live_nav_nippon_largecap_118632.csv"},
    {"code": 119092, "name": "Axis Bluechip Fund - Regular",          "file": "live_nav_axis_bluechip_119092.csv"},
    {"code": 120841, "name": "Kotak Bluechip Fund - Regular",         "file": "live_nav_kotak_bluechip_120841.csv"},
]

DIVIDER = "─" * 65


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fetch_scheme(code: int) -> dict:
    """
    GET https://api.mfapi.in/mf/{code}
    Returns the parsed JSON dict.
    Retries up to MAX_RETRY times on failure.
    """
    url = f"{API_BASE}/{code}"
    for attempt in range(1, MAX_RETRY + 1):
        try:
            print(f"  [GET] {url}  (attempt {attempt}/{MAX_RETRY})")
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            print(f"  [WARN] Attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRY:
                time.sleep(RETRY_WAIT)
    raise RuntimeError(f"All {MAX_RETRY} attempts failed for code {code}")


def parse_nav_data(raw_json: dict, amfi_code: int) -> pd.DataFrame:
    """
    Convert the mfapi.in JSON response into a clean DataFrame.
    mfapi.in structure:
      {
        "meta": { "fund_house": ..., "scheme_type": ..., "scheme_name": ... },
        "data": [{"date": "DD-MM-YYYY", "nav": "123.4567"}, ...]
      }
    """
    meta = raw_json.get("meta", {})
    records = raw_json.get("data", [])

    df = pd.DataFrame(records)

    # Parse date (mfapi returns DD-MM-YYYY)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    # Add metadata columns
    df.insert(0, "amfi_code",    amfi_code)
    df.insert(1, "scheme_name",  meta.get("scheme_name", ""))
    df.insert(2, "fund_house",   meta.get("fund_house",  ""))
    df.insert(3, "scheme_type",  meta.get("scheme_type", ""))

    # Sort by date ascending
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def fetch_and_save(scheme: dict) -> pd.DataFrame:
    """Fetch NAV for one scheme, save CSV, return DataFrame."""
    code = scheme["code"]
    name = scheme["name"]
    out_path = RAW_DIR / scheme["file"]

    print(f"\n{DIVIDER}")
    print(f"  Scheme : {name}  (code: {code})")
    print(DIVIDER)

    raw_json = fetch_scheme(code)
    df = parse_nav_data(raw_json, code)

    df.to_csv(out_path, index=False)

    print(f"  Rows   : {len(df):,}")
    print(f"  Date range : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Latest NAV : ₹ {df['nav'].iloc[-1]:.4f}  ({df['date'].iloc[-1].date()})")
    print(f"  Saved  → {out_path.name}")
    return df


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  BLUESTOCK FINTECH — LIVE NAV FETCH  (mfapi.in)")
    print("  Day 1 | Tasks 4 & 5")
    print("=" * 65)

    results = {}

    # ── Task 4: HDFC Top 100 ──────────────────────────────────────────────────
    print("\n[TASK 4] Fetching HDFC Top 100 (125497) — anchor scheme")
    try:
        df_hdfc = fetch_and_save(HDFC_TOP100)
        results[HDFC_TOP100["code"]] = df_hdfc

        # Print sample JSON structure for documentation
        raw_json = fetch_scheme(HDFC_TOP100["code"])
        print("\n  Raw JSON structure (first 2 records):")
        sample = {
            "meta": raw_json.get("meta", {}),
            "data": raw_json.get("data", [])[:2],
        }
        print("  " + json.dumps(sample, indent=4).replace("\n", "\n  "))
    except RuntimeError as e:
        print(f"  [ERROR] {e}")

    # ── Task 5: 5 Bluechip Schemes ────────────────────────────────────────────
    print("\n\n[TASK 5] Fetching 5 Bluechip schemes")
    for scheme in BLUECHIP_SCHEMES:
        try:
            df = fetch_and_save(scheme)
            results[scheme["code"]] = df
        except RuntimeError as e:
            print(f"  [ERROR] {e}")
        time.sleep(0.5)   # polite delay to mfapi.in

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'=' * 65}")
    print("  FETCH SUMMARY")
    print(f"{'=' * 65}")
    print(f"  {'Code':<10} {'Rows':>8}  {'From':<12}  {'To':<12}  Latest NAV")
    print(f"  {'-'*9} {'-'*8}  {'-'*12}  {'-'*12}  {'-'*14}")
    for code, df in results.items():
        name_short = df["scheme_name"].iloc[0][:35]
        print(
            f"  {code:<10} {len(df):>8,}  "
            f"{str(df['date'].min().date()):<12}  "
            f"{str(df['date'].max().date()):<12}  "
            f"₹ {df['nav'].iloc[-1]:.4f}"
        )
    print(f"\n  [✓] {len(results)} CSV files saved to data/raw/")
    return results


if __name__ == "__main__":
    nav_data = main()
