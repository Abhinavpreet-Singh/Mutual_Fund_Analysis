"""
run_pipeline.py
===============
Master pipeline controller for the Bluestock Mutual Fund Analytics Platform.
Executes the full end-to-end flow:
1. Live NAV Data Fetch (optional via --fetch-live)
2. Ingestion, Cleaning, and SQLite Database Creation (etl_pipeline.py)
3. Exploratory Data Analysis Chart Generation (day3_eda.py)
4. Performance & Risk Analytics Computations (compute_metrics.py)
"""

import argparse
import os
import sys
import subprocess
import time

# Resolve directory paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

DIVIDER = "=" * 75


def run_script(script_name: str, args_list: list[str] | None = None) -> bool:
    """
    Execute a python script in the scripts/ folder as a subprocess.
    
    Args:
        script_name: Filename of the target python script.
        args_list: List of optional CLI arguments to pass to the script.
        
    Returns:
        True if the script executed successfully (exit code 0), False otherwise.
    """
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return False
        
    cmd = [sys.executable, script_path] + (args_list or [])
    print(f"\n[RUNNING] {script_name}...")
    start_time = time.time()
    
    try:
        # Run subprocess and stream output directly to stdout/stderr
        result = subprocess.run(cmd, check=True)
        elapsed = time.time() - start_time
        print(f"[SUCCESS] {script_name} completed in {elapsed:.2f} seconds.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAILURE] {script_name} failed with exit code {e.returncode}.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Execution failed for {script_name}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Mutual Fund Analytics Master Pipeline")
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Fetch live NAV data from mfapi.in API (takes time and requires internet connection)"
    )
    args = parser.parse_args()
    
    print(DIVIDER)
    print("      BLUESTOCK MUTUAL FUND ANALYTICS — SYSTEM PIPELINE RUNNER")
    print(DIVIDER)
    pipeline_start = time.time()
    
    # Step 1: Live NAV Fetch (optional)
    if args.fetch_live:
        success = run_script("live_nav_fetch.py")
        if not success:
            print("[WARNING] Live NAV fetch failed. Continuing with existing raw datasets.")
    else:
        print("\n[INFO] Skipping live NAV fetch. Sourcing cached local raw data.")
        print("       (To pull fresh data from mfapi.in, run with the '--fetch-live' flag)")
        
    # Step 2: Run Consolidated ETL Pipeline (Ingest, Clean, SQLite)
    success = run_script("etl_pipeline.py")
    if not success:
        print("\n[FATAL] ETL Pipeline failed. Aborting pipeline execution.", file=sys.stderr)
        sys.exit(1)
        
    # Step 3: Run EDA Chart Generation
    success = run_script("day3_eda.py")
    if not success:
        print("\n[WARNING] EDA Visualizations failed. Continuing execution...")
        
    # Step 4: Run Performance & Risk metrics pipeline
    success = run_script("compute_metrics.py")
    if not success:
        print("\n[FATAL] Metrics Analytics failed. Aborting pipeline execution.", file=sys.stderr)
        sys.exit(1)
        
    elapsed = time.time() - pipeline_start
    print("\n" + DIVIDER)
    print(f"      PIPELINE EXECUTION COMPLETED IN {elapsed:.2f} SECONDS")
    print(DIVIDER)
    print("  All systems operational. Reports and figures have been updated in:")
    print("    - Cleaned CSVs  : data/processed/")
    print("    - SQLite Database: database/bluestock_mf.db")
    print("    - EDA Charts     : reports/day3_charts/")
    print("    - Day 4 Reports  : reports/day4/")
    print("    - Day 6 Reports  : reports/day6/")
    print("    - Key Deliverables copied to root for convenience.")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
