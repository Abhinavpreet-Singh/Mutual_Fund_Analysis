"""
scripts/live_nav_fetch.py
========================
Fetches live NAV from mfapi.in for specific schemes and saves raw CSV files.
Configured with pathing relative to the grandparent directory to run smoothly.
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://api.mfapi.in/mf"
TIMEOUT = 20          # seconds per request
RETRY_WAIT = 2        # seconds between retries
MAX_RETRY = 3

# Scheme Registry
HDFC_TOP100 = {
    "code": 125497,
    "name": "HDFC Top 100 Fund - Direct Plan - Growth",
    "file": "live_nav_hdfc_top100_125497.csv",
}

BLUECHIP_SCHEMES = [
    {"code": 119551, "name": "SBI Bluechip Fund - Regular", "file": "live_nav_sbi_bluechip_119551.csv"},
    {"code": 120503, "name": "ICICI Pru Bluechip Fund - Regular", "file": "live_nav_icici_bluechip_120503.csv"},
    {"code": 118632, "name": "Nippon India Large Cap Fund - Regular", "file": "live_nav_nippon_largecap_118632.csv"},
    {"code": 119092, "name": "Axis Bluechip Fund - Regular", "file": "live_nav_axis_bluechip_119092.csv"},
    {"code": 120841, "name": "Kotak Bluechip Fund - Regular", "file": "live_nav_kotak_bluechip_120841.csv"},
]

DIVIDER = "─" * 70


def fetch_scheme(code: int) -> dict:
    """GET requests to mfapi.in API with exponential retry backoff."""
    url = f"{API_BASE}/{code}"
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"    [WARN] Attempt {attempt}/{MAX_RETRY} failed for code {code}: {e}")
            if attempt < MAX_RETRY:
                time.sleep(RETRY_WAIT * attempt)
    raise RuntimeError(f"All {MAX_RETRY} attempts failed to fetch data for scheme {code}")


def parse_nav_data(raw_json: dict, amfi_code: int) -> pd.DataFrame:
    """Parse raw API JSON response into a clean DataFrame."""
    meta = raw_json.get("meta", {})
    records = raw_json.get("data", [])
    
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame()
        
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    
    df.insert(0, "amfi_code", amfi_code)
    df.insert(1, "scheme_name", meta.get("scheme_name", ""))
    df.insert(2, "fund_house", meta.get("fund_house", ""))
    df.insert(3, "scheme_type", meta.get("scheme_type", ""))
    
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def fetch_and_save(scheme: dict) -> pd.DataFrame:
    """Fetch NAV data for one scheme, write to raw directory, and return DataFrame."""
    code = scheme["code"]
    name = scheme["name"]
    out_path = RAW_DIR / scheme["file"]
    
    print(f"\n{DIVIDER}")
    print(f"  Fetching: {name} (AMFI Code: {code})")
    print(DIVIDER)
    
    raw_json = fetch_scheme(code)
    df = parse_nav_data(raw_json, code)
    
    if df.empty:
        print("    [WARNING] No records found.")
        return df
        
    df.to_csv(out_path, index=False)
    print(f"    Loaded {len(df):,} rows | Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"    Latest NAV: Rs. {df['nav'].iloc[-1]:.4f} ({df['date'].iloc[-1].date()})")
    print(f"    Saved raw file to {out_path.name}")
    return df


def main():
    print("=" * 70)
    print("  BLUESTOCK MUTUAL FUND ANALYTICS — LIVE NAV FETCH (mfapi.in)")
    print("=" * 70)
    
    results = {}
    
    # 1. Fetch HDFC Top 100 anchor scheme
    try:
        df_hdfc = fetch_and_save(HDFC_TOP100)
        if not df_hdfc.empty:
            results[HDFC_TOP100["code"]] = df_hdfc
    except Exception as e:
        print(f"  [ERROR] Failed to fetch HDFC Top 100: {e}")
        
    # 2. Fetch remaining 5 Bluechip schemes
    for scheme in BLUECHIP_SCHEMES:
        try:
            df = fetch_and_save(scheme)
            if not df.empty:
                results[scheme["code"]] = df
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {scheme['name']}: {e}")
        time.sleep(0.5)  # polite API delay
        
    # Print summary
    print(f"\n{DIVIDER}")
    print("  LIVE NAV FETCH SUMMARY")
    print(DIVIDER)
    if results:
        print(f"  {'Code':<10} {'Rows':>8}  {'Start Date':<12}  {'End Date':<12}  Latest NAV")
        print(f"  {'-'*9} {'-'*8}  {'-'*12}  {'-'*12}  {'-'*12}")
        for code, df in results.items():
            print(f"  {code:<10} {len(df):>8,}  {str(df['date'].min().date()):<12}  {str(df['date'].max().date()):<12}  Rs.{df['nav'].iloc[-1]:.2f}")
    else:
        print("  No live data was fetched (offline or API down). Pipeline will fall back to local raw data.")
    print("=" * 70)


if __name__ == "__main__":
    main()
