"""
scripts/portfolio_optimization.py
=================================
Calculates the Markowitz Efficient Frontier for 5 selected mutual funds:
1. Mirae Asset Large Cap Fund (148567)
2. ICICI Pru Midcap Fund (120505)
3. Kotak Flexicap Fund (120843)
4. HDFC Mid-Cap Opportunities Fund (100033)
5. ICICI Pru Bluechip Fund (120504)

Identifies the Maximum Sharpe Ratio (MSR) and Minimum Volatility (MVP) portfolios.
Exports the optimal allocations and generates the Efficient Frontier chart.
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
OUTPUT_DIR = REPORTS_DIR / "day6"
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

# Create target directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Visual Settings ─────────────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]


def load_historical_returns(selected_codes: list[int]) -> pd.DataFrame:
    """Fetch daily returns for selected funds from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Query daily NAV date and returns
    placeholders = ",".join("?" for _ in selected_codes)
    query = f"""
        SELECT nav_date as date, amfi_code, daily_return
        FROM fact_nav
        WHERE amfi_code IN ({placeholders})
        AND daily_return IS NOT NULL
        ORDER BY nav_date ASC
    """
    df = pd.read_sql_query(query, conn, params=selected_codes)
    conn.close()
    
    # Pivot returns to: index = date, columns = amfi_code
    returns_pivot = df.pivot(index="date", columns="amfi_code", values="daily_return").dropna()
    return returns_pivot


def run_portfolio_optimization(returns_df: pd.DataFrame, num_portfolios: int = 10000, rf_rate: float = 0.065):
    """
    Perform Monte Carlo simulation of random weights to map Efficient Frontier.
    
    Returns:
        results: Array containing [Return, Volatility, Sharpe Ratio, Weights...]
        weights_record: Array of portfolio weights
        optimal_portfolios: Dict of MSR and MVP weights and metrics
    """
    num_assets = len(returns_df.columns)
    
    # Calculate daily mean returns and covariance matrix
    mean_returns = returns_df.mean()
    cov_matrix = returns_df.cov()
    
    # Annualize (252 trading days)
    ann_returns = mean_returns * 252
    ann_cov = cov_matrix * 252
    
    # Results containers
    results = np.zeros((3 + num_assets, num_portfolios))
    weights_record = []
    
    # Seed for reproducibility
    np.random.seed(42)
    
    for i in range(num_portfolios):
        # Generate random weights summing to 1
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        weights_record.append(weights)
        
        # Portfolio Performance
        p_return = np.dot(weights, ann_returns)
        p_volatility = np.sqrt(np.dot(weights.T, np.dot(ann_cov, weights)))
        p_sharpe = (p_return - rf_rate) / p_volatility if p_volatility > 0 else 0
        
        results[0, i] = p_return
        results[1, i] = p_volatility
        results[2, i] = p_sharpe
        
        # Save weights in the results matrix
        for j in range(num_assets):
            results[3 + j, i] = weights[j]
            
    # Convert weights record to numpy array
    weights_record = np.array(weights_record)
    
    # Find MSR (Maximum Sharpe Ratio) index
    msr_idx = np.argmax(results[2])
    msr_return = results[0, msr_idx]
    msr_vol = results[1, msr_idx]
    msr_sharpe = results[2, msr_idx]
    msr_weights = results[3:, msr_idx]
    
    # Find MVP (Minimum Volatility Portfolio) index
    mvp_idx = np.argmin(results[1])
    mvp_return = results[0, mvp_idx]
    mvp_vol = results[1, mvp_idx]
    mvp_sharpe = results[2, mvp_idx]
    mvp_weights = results[3:, mvp_idx]
    
    optimal_portfolios = {
        "MSR": {
            "return": msr_return,
            "volatility": msr_vol,
            "sharpe": msr_sharpe,
            "weights": msr_weights
        },
        "MVP": {
            "return": mvp_return,
            "volatility": mvp_vol,
            "sharpe": mvp_sharpe,
            "weights": mvp_weights
        }
    }
    
    return results, optimal_portfolios, ann_returns, ann_cov


def plot_efficient_frontier(
    results: np.ndarray, 
    optimal: dict, 
    ann_returns: pd.Series, 
    ann_cov: pd.DataFrame, 
    fund_names: dict, 
    chart_path: Path
):
    """Save a beautiful static Markowitz Efficient Frontier scatter plot."""
    fig, ax = plt.subplots(figsize=(13, 8), dpi=150)
    fig.patch.set_facecolor('#fafafa')
    ax.set_facecolor('#ffffff')
    
    # 1. Scatter plot of simulated portfolios, color-coded by Sharpe Ratio
    scatter = ax.scatter(
        results[1] * 100,  # Volatility in %
        results[0] * 100,  # Return in %
        c=results[2],      # Sharpe Ratio
        cmap="viridis",
        alpha=0.4,
        s=8
    )
    
    # Add Colorbar
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Sharpe Ratio (Rf = 6.5%)", fontsize=11, color='#475569')
    cbar.ax.tick_params(labelsize=9)
    
    # 2. Mark Optimal Portfolios
    # Max Sharpe Ratio (MSR)
    ax.scatter(
        optimal["MSR"]["volatility"] * 100, 
        optimal["MSR"]["return"] * 100, 
        color="#DC2626", 
        marker="*", 
        s=250, 
        label=f"Max Sharpe Ratio ({optimal['MSR']['sharpe']:.2f})", 
        edgecolor="black", 
        zorder=10
    )
    # Min Volatility (MVP)
    ax.scatter(
        optimal["MVP"]["volatility"] * 100, 
        optimal["MVP"]["return"] * 100, 
        color="#2563EB", 
        marker="D", 
        s=120, 
        label=f"Min Volatility ({optimal['MVP']['volatility']*100:.2f}%)", 
        edgecolor="black", 
        zorder=10
    )
    
    # 3. Mark Individual Funds
    for code, ret in ann_returns.items():
        vol = np.sqrt(ann_cov.loc[code, code])
        name = fund_names.get(code, str(code)).split(" - ")[0]
        ax.scatter(vol * 100, ret * 100, color="#0F766E", marker="o", s=80, edgecolor="black", zorder=5)
        ax.annotate(
            name, 
            (vol * 100, ret * 100), 
            textcoords="offset points", 
            xytext=(10, -5), 
            ha='left', 
            fontsize=8, 
            fontweight='semibold',
            color='#0f172a'
        )
        
    ax.set_title("Markowitz Efficient Frontier & Portfolio Optimization", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Annualized Volatility / Risk (%)", fontsize=11, color='#475569')
    ax.set_ylabel("Annualized Expected Return (%)", fontsize=11, color='#475569')
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=10)
    
    plt.savefig(chart_path, bbox_inches="tight", facecolor='#fafafa')
    plt.close()


def main():
    print("\n" + "=" * 75)
    print("      BLUESTOCK MF ANALYTICS — PORTFOLIO OPTIMIZATION MODULE")
    print("=" * 75)
    
    if not DB_PATH.exists():
        print(f"[FATAL] SQLite Database not found at: {DB_PATH.resolve()}")
        return
        
    # Selected codes for optimization
    selected_codes = [148567, 120505, 120843, 100033, 120504]
    
    # Load Fund names for plotting
    conn = sqlite3.connect(DB_PATH)
    placeholders = ",".join("?" for _ in selected_codes)
    names_df = pd.read_sql_query(
        f"SELECT amfi_code, scheme_name FROM dim_fund WHERE amfi_code IN ({placeholders})", 
        conn, 
        params=selected_codes
    )
    conn.close()
    fund_names = dict(zip(names_df["amfi_code"], names_df["scheme_name"]))
    
    print("Loading historical Daily Returns from database...")
    returns_df = load_historical_returns(selected_codes)
    
    if len(returns_df) < 50:
        print(f"[FATAL] Insufficient daily observations ({len(returns_df)}) for asset optimization.")
        return
        
    print(f"Running Markowitz optimization (10,000 simulations) on {len(selected_codes)} assets...")
    results, optimal, ann_returns, ann_cov = run_portfolio_optimization(returns_df, num_portfolios=10000)
    
    # Export optimal portfolio weights
    records = []
    for port_type, data in optimal.items():
        record = {
            "portfolio_type": port_type,
            "expected_annual_return_pct": data["return"] * 100,
            "annual_volatility_pct": data["volatility"] * 100,
            "sharpe_ratio": data["sharpe"]
        }
        for idx, code in enumerate(selected_codes):
            name = fund_names.get(code, str(code))
            record[f"weight_{name.split(' - ')[0].replace(' ', '_')}"] = data["weights"][idx] * 100
        records.append(record)
        
    out_df = pd.DataFrame(records)
    out_path = OUTPUT_DIR / "portfolio_optimization_results.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Optimal portfolio weights saved to: {out_path}")
    
    # Generate static chart
    chart_path = OUTPUT_DIR / "efficient_frontier.png"
    plot_efficient_frontier(results, optimal, ann_returns, ann_cov, fund_names, chart_path)
    print(f"Efficient Frontier chart generated at: {chart_path}")
    
    # Output Console summary
    print("\n--- Portfolio Optimization Summary ---")
    for port in ["MSR", "MVP"]:
        print(f"\n{port} Portfolio:")
        print(f"  Expected Return: {optimal[port]['return']*100:.2f}%")
        print(f"  Volatility/Risk: {optimal[port]['volatility']*100:.2f}%")
        print(f"  Sharpe Ratio:    {optimal[port]['sharpe']:.2f}")
        print("  Asset Allocations:")
        for idx, code in enumerate(selected_codes):
            name = fund_names.get(code, str(code)).split(" - ")[0]
            print(f"    - {name}: {optimal[port]['weights'][idx]*100:.2f}%")
            
    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()
