"""
scripts/compute_metrics.py
==========================
Consolidated metrics computation pipeline.
Calculates performance, risk, and concentration metrics for Day 4 and Day 6,
updates the SQLite database table fact_performance, and exports reports and charts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress

# ─── Path Configuration ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
DAY4_REPORTS_DIR = REPORTS_DIR / "day4"
DAY6_REPORTS_DIR = REPORTS_DIR / "day6"
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

# Create target directories
DAY4_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DAY6_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Visual Settings ─────────────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]


# ─── Part 1: Day 4 Performance Metrics ────────────────────────────────────────
def calculate_performance_metrics():
    """Compute performance indicators, build composite scorecard, and update SQLite database."""
    print("\n[PART 1] Running Day 4 Fund Performance Analytics...")
    
    # Load data
    nav_df = pd.read_csv(PROCESSED_DIR / "clean_nav.csv", parse_dates=["date"])
    master_df = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
    bench_df = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv", parse_dates=["date"])
    
    fund_names = master_df.set_index("amfi_code")["scheme_name"].to_dict()
    fund_categories = master_df.set_index("amfi_code")["category"].to_dict()
    fund_expenses = master_df.set_index("amfi_code")["expense_ratio_pct"].to_dict()
    
    # 1. Daily Returns
    nav_pivot = nav_df.pivot(index="date", columns="amfi_code", values="nav").sort_index()
    daily_returns = nav_pivot.pct_change()
    
    returns_computed_df = nav_df.sort_values(["amfi_code", "date"]).copy()
    returns_computed_df["daily_return"] = returns_computed_df.groupby("amfi_code")["nav"].pct_change()
    returns_computed_df.to_csv(DAY4_REPORTS_DIR / "returns_computed.csv", index=False)
    
    # 2. CAGR (1yr, 3yr, 5yr)
    latest_date = nav_pivot.index.max()
    cagr_results = []
    
    for code in nav_pivot.columns:
        fund_nav = nav_pivot[code].dropna()
        if fund_nav.empty:
            continue
        
        val_end = fund_nav.loc[latest_date] if latest_date in fund_nav.index else fund_nav.iloc[-1]
        date_end = fund_nav.index[-1]
        
        # 1 Year CAGR
        target_1yr = date_end - pd.DateOffset(years=1)
        available_1yr = fund_nav.index[fund_nav.index <= target_1yr]
        cagr_1yr = (val_end / fund_nav.loc[available_1yr[-1]]) ** (1 / ((date_end - available_1yr[-1]).days / 365.25)) - 1 if len(available_1yr) > 0 else np.nan
            
        # 3 Year CAGR
        target_3yr = date_end - pd.DateOffset(years=3)
        available_3yr = fund_nav.index[fund_nav.index <= target_3yr]
        cagr_3yr = (val_end / fund_nav.loc[available_3yr[-1]]) ** (1 / ((date_end - available_3yr[-1]).days / 365.25)) - 1 if len(available_3yr) > 0 else np.nan
            
        # 5 Year CAGR (using maximum history)
        date_start_5yr = fund_nav.index[0]
        val_start_5yr = fund_nav.iloc[0]
        n_years_5yr = (date_end - date_start_5yr).days / 365.25
        cagr_5yr = (val_end / val_start_5yr) ** (1 / n_years_5yr) - 1
        
        cagr_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "cagr_1yr_pct": cagr_1yr * 100,
            "cagr_3yr_pct": cagr_3yr * 100,
            "cagr_5yr_pct": cagr_5yr * 100,
            "history_years": n_years_5yr
        })
        
    cagr_report_df = pd.DataFrame(cagr_results)
    cagr_report_df.to_csv(DAY4_REPORTS_DIR / "cagr_report.csv", index=False)
    
    # 3. Sharpe & Sortino
    rf_annual = 0.065
    sharpe_results = []
    sortino_results = []
    vol_results = {}
    
    for code in daily_returns.columns:
        ret_series = daily_returns[code].dropna()
        if len(ret_series) == 0:
            continue
            
        rp_annual = ret_series.mean() * 252
        vol_annual = ret_series.std() * np.sqrt(252)
        vol_results[code] = ret_series.std()
        
        sharpe = (rp_annual - rf_annual) / vol_annual if vol_annual > 0 else np.nan
        sharpe_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "sharpe_ratio": sharpe
        })
        
        neg_returns = ret_series[ret_series < 0]
        downside_std_annual = neg_returns.std() * np.sqrt(252)
        sortino = (rp_annual - rf_annual) / downside_std_annual if downside_std_annual > 0 else np.nan
        sortino_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "sortino_ratio": sortino
        })
        
    sharpe_df = pd.DataFrame(sharpe_results)
    sharpe_df.to_csv(DAY4_REPORTS_DIR / "sharpe_values.csv", index=False)
    
    sortino_df = pd.DataFrame(sortino_results)
    sortino_df.to_csv(DAY4_REPORTS_DIR / "sortino_values.csv", index=False)
    
    # 4. Alpha & Beta
    nifty100_df = bench_df[bench_df["index_name"] == "NIFTY100"].sort_values("date").copy()
    nifty100_df["benchmark_return"] = nifty100_df["close_value"].pct_change()
    nifty_returns = nifty100_df.set_index("date")["benchmark_return"].dropna()
    
    alpha_beta_results = []
    for code in daily_returns.columns:
        ret_series = daily_returns[code].dropna()
        merged = pd.concat([ret_series, nifty_returns], axis=1, join="inner").dropna()
        
        if len(merged) < 5:
            alpha_beta_results.append({"amfi_code": code, "scheme_name": fund_names.get(code, "Unknown"), "alpha": np.nan, "beta": np.nan})
            continue
            
        slope, intercept, _, _, _ = linregress(merged.iloc[:, 1], merged.iloc[:, 0])
        alpha_beta_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "alpha": intercept * 252,
            "beta": slope
        })
        
    alpha_beta_df = pd.DataFrame(alpha_beta_results)
    alpha_beta_df.to_csv(DAY4_REPORTS_DIR / "alpha_beta.csv", index=False)
    
    # 5. Maximum Drawdown
    dd_results = []
    for code in nav_pivot.columns:
        fund_nav = nav_pivot[code].dropna()
        if fund_nav.empty:
            continue
        running_max = fund_nav.cummax()
        drawdowns = fund_nav / running_max - 1
        max_dd = drawdowns.min()
        dd_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "max_drawdown_pct": max_dd * 100
        })
    dd_df = pd.DataFrame(dd_results)
    dd_df.to_csv(DAY4_REPORTS_DIR / "max_drawdown.csv", index=False)
    
    # 6. Composite Scorecard
    scorecard = cagr_report_df[["amfi_code", "scheme_name", "cagr_3yr_pct"]].copy()
    scorecard = scorecard.merge(sharpe_df[["amfi_code", "sharpe_ratio"]], on="amfi_code")
    scorecard = scorecard.merge(alpha_beta_df[["amfi_code", "alpha"]], on="amfi_code")
    scorecard = scorecard.merge(dd_df[["amfi_code", "max_drawdown_pct"]], on="amfi_code")
    scorecard["expense_ratio_pct"] = scorecard["amfi_code"].map(fund_expenses)
    scorecard["category"] = scorecard["amfi_code"].map(fund_categories)
    
    clean_scorecard = scorecard.dropna().copy()
    clean_scorecard["rank_3yr"] = clean_scorecard["cagr_3yr_pct"].rank(pct=True) * 100
    clean_scorecard["rank_sharpe"] = clean_scorecard["sharpe_ratio"].rank(pct=True) * 100
    clean_scorecard["rank_alpha"] = clean_scorecard["alpha"].rank(pct=True) * 100
    clean_scorecard["rank_expense_inv"] = clean_scorecard["expense_ratio_pct"].rank(ascending=False, pct=True) * 100
    clean_scorecard["rank_max_dd_inv"] = clean_scorecard["max_drawdown_pct"].rank(ascending=True, pct=True) * 100
    
    clean_scorecard["composite_score"] = (
        0.30 * clean_scorecard["rank_3yr"] +
        0.25 * clean_scorecard["rank_sharpe"] +
        0.20 * clean_scorecard["rank_alpha"] +
        0.15 * clean_scorecard["rank_expense_inv"] +
        0.10 * clean_scorecard["rank_max_dd_inv"]
    )
    clean_scorecard = clean_scorecard.sort_values("composite_score", ascending=False).reset_index(drop=True)
    clean_scorecard["final_rank"] = clean_scorecard.index + 1
    clean_scorecard.to_csv(DAY4_REPORTS_DIR / "fund_scorecard.csv", index=False)
    
    # 7. Tracking Error & Benchmark Comparisons
    top_5 = clean_scorecard.head(5)
    te_results = []
    for code in top_5["amfi_code"]:
        fund_ret = daily_returns[code].dropna()
        merged = pd.concat([fund_ret, nifty_returns], axis=1, join="inner").dropna()
        diff = merged.iloc[:, 0] - merged.iloc[:, 1]
        te = diff.std() * np.sqrt(252)
        te_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "tracking_error_nifty100_pct": te * 100
        })
    te_df = pd.DataFrame(te_results)
    te_df.to_csv(DAY4_REPORTS_DIR / "tracking_errors.csv", index=False)
    
    # Plot benchmark comparison
    top_5_codes = top_5["amfi_code"].tolist()
    start_date = latest_date - pd.DateOffset(years=3)
    nav_subset = nav_pivot[top_5_codes].loc[start_date:latest_date].ffill()
    nav_indexed = nav_subset.div(nav_subset.iloc[0]) * 100
    
    bench_pivot = bench_df[bench_df["index_name"].isin(["NIFTY50", "NIFTY100"])].pivot(index="date", columns="index_name", values="close_value")
    bench_subset = bench_pivot.loc[start_date:latest_date].ffill()
    bench_indexed = bench_subset.div(bench_subset.iloc[0]) * 100
    
    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
    fig.patch.set_facecolor('#fafafa')
    ax.set_facecolor('#ffffff')
    for idx, code in enumerate(top_5_codes):
        ax.plot(nav_indexed.index, nav_indexed[code], label=fund_names[code].split(" - ")[0], color=COLORS[idx % len(COLORS)], linewidth=2)
    ax.plot(bench_indexed.index, bench_indexed["NIFTY50"], label="NIFTY 50", color="#10B981", linestyle="--", linewidth=2.5)
    ax.plot(bench_indexed.index, bench_indexed["NIFTY100"], label="NIFTY 100", color="#4B5563", linestyle="-.", linewidth=2.5)
    ax.set_title("Top 5 Mutual Funds vs Benchmark Indices (3-Year Indexed Cumulative Performance)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Date", fontsize=11, color='#475569')
    ax.set_ylabel("Indexed Value (Base = 100)", fontsize=11, color='#475569')
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    
    chart_path = DAY4_REPORTS_DIR / "benchmark_comparison_chart.png"
    plt.savefig(chart_path, bbox_inches="tight", facecolor='#fafafa')
    plt.savefig(DAY4_REPORTS_DIR / "benchmark_chart.png", bbox_inches="tight", facecolor='#fafafa')
    plt.close()
    
    # Update SQLite database
    if DB_PATH.exists():
        print("  Updating fact_performance table in bluestock_mf.db...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for _, row in clean_scorecard.iterrows():
            code = int(row["amfi_code"])
            c1 = float(cagr_report_df[cagr_report_df["amfi_code"] == code]["cagr_1yr_pct"].values[0])
            c3 = float(row["cagr_3yr_pct"])
            c5 = float(cagr_report_df[cagr_report_df["amfi_code"] == code]["cagr_5yr_pct"].values[0])
            a = float(row["alpha"])
            b = float(alpha_beta_df[alpha_beta_df["amfi_code"] == code]["beta"].values[0])
            s = float(row["sharpe_ratio"])
            so = float(sortino_df[sortino_df["amfi_code"] == code]["sortino_ratio"].values[0])
            sd = float(vol_results.get(code, np.nan) * np.sqrt(252) * 100)
            m = float(row["max_drawdown_pct"])
            
            cursor.execute("SELECT 1 FROM fact_performance WHERE amfi_code = ?", (code,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE fact_performance
                    SET return_1yr_pct = ?, return_3yr_pct = ?, return_5yr_pct = ?,
                        alpha = ?, beta = ?, sharpe_ratio = ?, sortino_ratio = ?,
                        std_dev_ann_pct = ?, max_drawdown_pct = ?
                    WHERE amfi_code = ?
                """, (c1, c3, c5, a, b, s, so, sd, m, code))
        conn.commit()
        conn.close()
        print("  SQLite database metrics successfully updated.")
        
    print(f"  [SUCCESS] Day 4 Performance calculations complete. Saved outputs to {DAY4_REPORTS_DIR}")


# ─── Part 2: Day 6 Advanced Analytics + Risk ──────────────────────────────────
def calculate_advanced_metrics():
    """Compute risk assessment indicators (VaR, CVaR, HHI, cohort metrics, and churn flags)."""
    print("\n[PART 2] Running Day 6 Advanced Analytics & Risk Metrics...")
    
    conn = sqlite3.connect(DB_PATH)
    dim_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    fact_nav = pd.read_sql_query("SELECT * FROM fact_nav", conn)
    fact_transactions = pd.read_sql_query("SELECT * FROM fact_transactions", conn)
    fact_holdings = pd.read_sql_query("SELECT * FROM fact_holdings", conn)
    conn.close()
    
    # 1. Historical VaR & CVaR
    var_cvar_results = []
    for code, group in fact_nav.groupby("amfi_code"):
        returns = group["daily_return"].dropna()
        if len(returns) == 0:
            continue
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()
        scheme_name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0]
        var_cvar_results.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "var_95_pct": -var_95 * 100,
            "cvar_95_pct": -cvar_95 * 100
        })
    var_cvar_df = pd.DataFrame(var_cvar_results).sort_values("var_95_pct", ascending=False).reset_index(drop=True)
    var_cvar_df.to_csv(DAY6_REPORTS_DIR / "var_cvar_report.csv", index=False)
    var_cvar_df.to_csv(BASE_DIR / "var_cvar_report.csv", index=False)
    
    # 2. Rolling 90-day Sharpe Ratio
    nav_pivot = fact_nav.pivot(index="nav_date", columns="amfi_code", values="daily_return").sort_index()
    selected_codes = [148567, 120505, 120843, 100033, 120504]
    selected_codes = [c for c in selected_codes if c in nav_pivot.columns]
    
    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
    fig.patch.set_facecolor('#fafafa')
    ax.set_facecolor('#ffffff')
    for idx, code in enumerate(selected_codes):
        fund_returns = nav_pivot[code].dropna()
        rolling_mean = fund_returns.rolling(90).mean()
        rolling_std = fund_returns.rolling(90).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
        rolling_sharpe = rolling_sharpe.dropna()
        
        name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0].split(" - ")[0]
        dates = pd.to_datetime(rolling_sharpe.index)
        ax.plot(dates, rolling_sharpe, label=name, color=COLORS[idx % len(COLORS)], linewidth=2)
        
    ax.set_title("Rolling 90-day Sharpe Ratio over Time (Top 5 scorecard funds)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Date", fontsize=11, color='#475569')
    ax.set_ylabel("Rolling Sharpe Ratio (Annualized)", fontsize=11, color='#475569')
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    
    plt.savefig(DAY6_REPORTS_DIR / "rolling_sharpe_chart.png", bbox_inches="tight", facecolor='#fafafa')
    plt.savefig(BASE_DIR / "rolling_sharpe_chart.png", bbox_inches="tight", facecolor='#fafafa')
    plt.close()
    
    # 3. Cohort Analysis
    fact_transactions["transaction_date"] = pd.to_datetime(fact_transactions["transaction_date"])
    first_txn = fact_transactions.groupby("investor_id")["transaction_date"].min().reset_index()
    first_txn.columns = ["investor_id", "first_txn_date"]
    first_txn["cohort_year"] = first_txn["first_txn_date"].dt.year
    tx_cohorts = fact_transactions.merge(first_txn[["investor_id", "cohort_year"]], on="investor_id")
    
    cohort_results = []
    for year, group in tx_cohorts.groupby("cohort_year"):
        investor_count = group["investor_id"].nunique()
        sip_group = group[group["transaction_type"] == "SIP"]
        avg_sip = sip_group["amount_inr"].mean() if not sip_group.empty else 0.0
        total_invested = group[group["transaction_type"] != "Redemption"]["amount_inr"].sum()
        
        merged_with_fund = group.merge(dim_fund[["amfi_code", "category"]], on="amfi_code")
        pref_cat = merged_with_fund.groupby("category")["amount_inr"].sum().idxmax() if not merged_with_fund.empty else "None"
        cohort_results.append({
            "cohort_year": int(year),
            "total_investors": investor_count,
            "avg_sip_amount": avg_sip,
            "total_invested_amount": total_invested,
            "preferred_category": pref_cat
        })
    cohort_df = pd.DataFrame(cohort_results)
    cohort_df.to_csv(DAY6_REPORTS_DIR / "cohort_analysis.csv", index=False)
    
    # 4. SIP Continuation
    sip_tx = fact_transactions[fact_transactions["transaction_type"] == "SIP"].copy()
    sip_tx = sip_tx.sort_values(["investor_id", "transaction_date"])
    continuity_results = []
    for investor_id, group in sip_tx.groupby("investor_id"):
        txn_count = len(group)
        if txn_count < 6:
            continue
        dates = group["transaction_date"].sort_values()
        gaps = dates.diff().dropna().dt.days
        avg_gap = gaps.mean()
        max_gap = gaps.max()
        at_risk = 1 if avg_gap > 35 else 0
        continuity_results.append({
            "investor_id": investor_id,
            "total_sip_transactions": txn_count,
            "avg_gap_days": avg_gap,
            "max_gap_days": max_gap,
            "at_risk_flag": at_risk
        })
    continuity_df = pd.DataFrame(continuity_results)
    continuity_df.to_csv(DAY6_REPORTS_DIR / "sip_continuity.csv", index=False)
    
    # 5. Sector Concentration HHI
    hhi_results = []
    for code, group in fact_holdings.groupby("amfi_code"):
        scheme_name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0]
        cat = dim_fund[dim_fund["amfi_code"] == code]["category"].values[0]
        if cat != "Equity":
            continue
        sector_weights = group.groupby("sector")["weight_pct"].sum()
        if sector_weights.sum() > 0:
            norm_weights = sector_weights / sector_weights.sum() * 100
            hhi = np.sum(norm_weights ** 2)
        else:
            hhi = np.nan
            
        if hhi > 2500:
            level = "Highly Concentrated"
        elif hhi >= 1500:
            level = "Moderately Concentrated"
        else:
            level = "Diverse"
            
        hhi_results.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "sector_hhi": hhi,
            "concentration_level": level
        })
    hhi_df = pd.DataFrame(hhi_results).sort_values("sector_hhi", ascending=False).reset_index(drop=True)
    hhi_df.to_csv(DAY6_REPORTS_DIR / "sector_hhi.csv", index=False)
    
    # Plot HHI
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    fig.patch.set_facecolor('#fafafa')
    ax.set_facecolor('#ffffff')
    plot_hhi = hhi_df.head(15)
    ax.bar(plot_hhi["scheme_name"].apply(lambda x: x.split(" - ")[0]), plot_hhi["sector_hhi"], color=COLORS[0], width=0.5)
    ax.axhline(2500, color=COLORS[3], linestyle="--", label="Highly Concentrated (>2500)")
    ax.axhline(1500, color=COLORS[4], linestyle="--", label="Moderately Concentrated (1500-2500)")
    ax.set_title("Sector Concentration Risk (Herfindahl-Hirschman Index - HHI)", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Scheme Name", fontsize=10, color='#475569')
    ax.set_ylabel("Sector HHI Score", fontsize=10, color='#475569')
    ax.tick_params(axis='x', rotation=30, labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    
    plt.savefig(DAY6_REPORTS_DIR / "sector_hhi_chart.png", bbox_inches="tight", facecolor='#fafafa')
    plt.close()
    
    print(f"  [SUCCESS] Day 6 Risk and advanced calculations complete. Saved outputs to {DAY6_REPORTS_DIR}")


def main():
    print("=" * 75)
    print("BLUESTOCK MUTUAL FUND ANALYTICS — CONSOLIDATED METRICS PIPELINE")
    print("=" * 75)
    
    # Day 4
    calculate_performance_metrics()
    
    # Day 6
    calculate_advanced_metrics()
    
    print("\n[SUCCESS] All metric computations and reports successfully completed.")
    print("=" * 75)


if __name__ == "__main__":
    main()
