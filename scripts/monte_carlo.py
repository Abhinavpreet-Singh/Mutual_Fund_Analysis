"""
scripts/monte_carlo.py
======================
Implements a Monte Carlo simulation engine for Mutual Fund NAV projections.
Projects NAV growth over 5 years (1260 trading days) with uncertainty bands
(5th, 25th, 50th, 75th, 95th percentiles) and exports summary statistics and charts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ─── Path Configuration ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
MONTE_CARLO_DIR = REPORTS_DIR / "day6"
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

# Create target directories
MONTE_CARLO_DIR.mkdir(parents=True, exist_ok=True)

# ─── Visual Settings ─────────────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]


def run_monte_carlo(
    amfi_code: int, 
    scheme_name: str, 
    n_simulations: int = 1000, 
    projection_years: int = 5
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Run a Monte Carlo simulation for a specific fund using Geometric Brownian Motion.
    
    Args:
        amfi_code: AMFI code of the mutual fund.
        scheme_name: Name of the mutual fund.
        n_simulations: Number of random path simulations.
        projection_years: Number of years to project (252 trading days/year).
        
    Returns:
        historical_df: Historical daily NAV data.
        projection_df: Simulation percentiles over the projection horizon.
        metrics: Dictionary of summary simulation metrics.
    """
    # 1. Fetch historical NAVs
    conn = sqlite3.connect(DB_PATH)
    nav_query = """
        SELECT nav_date, nav
        FROM fact_nav
        WHERE amfi_code = ?
        ORDER BY nav_date ASC
    """
    hist_df = pd.read_sql_query(nav_query, conn, params=(amfi_code,))
    conn.close()
    
    if len(hist_df) < 30:
        raise ValueError(f"Insufficient historical data for fund {amfi_code}")
        
    hist_df["nav_date"] = pd.to_datetime(hist_df["nav_date"])
    hist_df = hist_df.sort_values("nav_date").reset_index(drop=True)
    
    # Calculate daily log returns
    hist_df["log_return"] = np.log(hist_df["nav"] / hist_df["nav"].shift(1))
    log_returns = hist_df["log_return"].dropna()
    
    # Calculate drift and volatility parameters
    mu = log_returns.mean()
    sigma = log_returns.std()
    
    # Latest NAV
    latest_nav = hist_df["nav"].iloc[-1]
    latest_date = hist_df["nav_date"].iloc[-1]
    
    # 2. Simulation setup
    trading_days = int(projection_years * 252)
    
    # Seed for reproducibility
    np.random.seed(42)
    
    # Generate daily increments: exp((mu - 0.5 * sigma^2) + sigma * Z)
    # Using empirical mean of log returns directly represents (mu - 0.5 * sigma^2)
    daily_shocks = np.random.normal(loc=mu, scale=sigma, size=(trading_days, n_simulations))
    
    # Cumulative return paths
    # Add a row of zeros at the start for the initial state (t=0)
    path_returns = np.vstack([np.zeros(n_simulations), daily_shocks])
    cum_returns = np.exp(np.cumsum(path_returns, axis=0))
    
    # NAV paths: shape (trading_days + 1, n_simulations)
    nav_paths = latest_nav * cum_returns
    
    # 3. Calculate percentiles
    percentiles = [5, 25, 50, 75, 95]
    pct_values = np.percentile(nav_paths, percentiles, axis=1) # shape (5, trading_days + 1)
    
    # Create projection dates (working days)
    proj_dates = pd.date_range(start=latest_date + pd.Timedelta(days=1), periods=trading_days, freq="B")
    proj_dates = [latest_date] + list(proj_dates) # Add t=0 date
    
    proj_df = pd.DataFrame({
        "date": proj_dates,
        "p5": pct_values[0],
        "p25": pct_values[1],
        "p50": pct_values[2],
        "p75": pct_values[3],
        "p95": pct_values[4]
    })
    
    # 4. Simulation Metrics
    final_navs = nav_paths[-1, :]
    expected_cagr = ((np.mean(final_navs) / latest_nav) ** (1 / projection_years) - 1) * 100
    prob_positive = np.mean(final_navs > latest_nav) * 100
    median_final_nav = np.median(final_navs)
    worst_case_nav = pct_values[0][-1]  # 5th percentile
    best_case_nav = pct_values[4][-1]   # 95th percentile
    
    metrics = {
        "amfi_code": amfi_code,
        "scheme_name": scheme_name,
        "latest_nav": latest_nav,
        "mean_final_nav": np.mean(final_navs),
        "median_final_nav": median_final_nav,
        "worst_case_nav_5pct": worst_case_nav,
        "best_case_nav_95pct": best_case_nav,
        "expected_5yr_cagr_pct": expected_cagr,
        "prob_positive_return_pct": prob_positive,
        "ann_historical_vol_pct": sigma * np.sqrt(252) * 100
    }
    
    return hist_df, proj_df, metrics


def plot_monte_carlo(
    hist_df: pd.DataFrame, 
    proj_df: pd.DataFrame, 
    scheme_name: str, 
    chart_path: Path
):
    """Generate and save a premium chart showing history and projection bands."""
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150)
    fig.patch.set_facecolor('#fafafa')
    ax.set_facecolor('#ffffff')
    
    # Plot historical data (last 1.5 years for context readability)
    hist_subset = hist_df.tail(252 * 2) # last 2 years
    ax.plot(hist_subset["nav_date"], hist_subset["nav"], color="#0F766E", label="Historical NAV", linewidth=2.5)
    
    # Plot projection median
    ax.plot(proj_df["date"], proj_df["p50"], color="#2563EB", label="Projected Median (p50)", linewidth=2.5)
    
    # Fill uncertainty bands
    # p25 to p75
    ax.fill_between(
        proj_df["date"], proj_df["p25"], proj_df["p75"], 
        color="#2563EB", alpha=0.15, label="Interquartile Range (p25-p75)"
    )
    
    # p5 to p95
    ax.fill_between(
        proj_df["date"], proj_df["p5"], proj_df["p95"], 
        color="#2563EB", alpha=0.06, linestyle="--", edgecolor="#3b82f6", label="90% Confidence Interval (p5-p95)"
    )
    
    # Customize layout
    clean_name = scheme_name.split(" - ")[0]
    ax.set_title(f"5-Year Monte Carlo NAV Projection: {clean_name}", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Date", fontsize=11, color='#475569')
    ax.set_ylabel("NAV (INR)", fontsize=11, color='#475569')
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    
    # Format x-axis dates nicely
    fig.autofmt_xdate()
    
    plt.savefig(chart_path, bbox_inches="tight", facecolor='#fafafa')
    plt.close()


def main():
    print("\n" + "=" * 75)
    print("      BLUESTOCK MF ANALYTICS — MONTE CARLO SIMULATION ENGINE")
    print("=" * 75)
    
    if not DB_PATH.exists():
        print(f"[FATAL] SQLite Database not found at: {DB_PATH.resolve()}")
        return
        
    # Load Top 5 funds from scorecard to generate charts for
    scorecard_path = BASE_DIR / "reports" / "day4" / "fund_scorecard.csv"
    if not scorecard_path.exists():
        print("[WARNING] Day 4 Scorecard csv not found. Defaulting to first 5 funds in dim_fund.")
        conn = sqlite3.connect(DB_PATH)
        funds_df = pd.read_sql_query("SELECT amfi_code, scheme_name FROM dim_fund LIMIT 5", conn)
        conn.close()
    else:
        scorecard = pd.read_csv(scorecard_path)
        funds_df = scorecard[["amfi_code", "scheme_name"]].head(5)
        
    all_summary_metrics = []
    
    for idx, row in funds_df.iterrows():
        code = int(row["amfi_code"])
        name = row["scheme_name"]
        print(f"Running 5-year Monte Carlo simulation (1,000 trials) for: {name.split(' - ')[0]}...")
        
        try:
            hist_df, proj_df, metrics = run_monte_carlo(code, name, n_simulations=1000, projection_years=5)
            all_summary_metrics.append(metrics)
            
            # Save chart
            chart_file = MONTE_CARLO_DIR / f"monte_carlo_{code}.png"
            plot_monte_carlo(hist_df, proj_df, name, chart_file)
            
            # Save raw projection data
            proj_df.to_csv(MONTE_CARLO_DIR / f"monte_carlo_raw_{code}.csv", index=False)
            
        except Exception as e:
            print(f"  [ERROR] Failed to run simulation for {code}: {e}")
            
    # Export summary report
    summary_df = pd.DataFrame(all_summary_metrics)
    summary_df.to_csv(MONTE_CARLO_DIR / "monte_carlo_summary.csv", index=False)
    print(f"\n[SUCCESS] Monte Carlo projections completed successfully!")
    print(f"          Reports and charts exported to: {MONTE_CARLO_DIR}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
