import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from pathlib import Path

# Setup paths
BASE_DIR = Path("c:/repo/Mutual_Fund_Analysis")
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
DAY4_REPORTS_DIR = REPORTS_DIR / "day4"
DB_DIR = BASE_DIR / "database"

# Create directories if they don't exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DAY4_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bluestock_mf.db"

# Create directories if they don't exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("Starting Fund Performance Analytics (Day 4)...")

# 1. Load Data
nav_df = pd.read_csv(PROCESSED_DIR / "clean_nav.csv", parse_dates=["date"])
master_df = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
bench_df = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv", parse_dates=["date"])

fund_names = master_df.set_index("amfi_code")["scheme_name"].to_dict()
fund_categories = master_df.set_index("amfi_code")["category"].to_dict()
fund_expenses = master_df.set_index("amfi_code")["expense_ratio_pct"].to_dict()

# 2. Pivot NAV for daily returns calculation
nav_pivot = nav_df.pivot(index="date", columns="amfi_code", values="nav").sort_index()

# 3. Compute Daily Returns
daily_returns = nav_pivot.pct_change()

# Save daily returns to returns_computed.csv in long format
returns_computed_df = nav_df.sort_values(["amfi_code", "date"]).copy()
returns_computed_df["daily_return"] = returns_computed_df.groupby("amfi_code")["nav"].pct_change()
returns_computed_df.to_csv(DAY4_REPORTS_DIR / "returns_computed.csv", index=False)
print("[1] Saved returns_computed.csv to reports/day4")

# 4. Calculate CAGR for 1yr, 3yr, 5yr (proxy) periods
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
    if len(available_1yr) > 0:
        date_start_1yr = available_1yr[-1]
        val_start_1yr = fund_nav.loc[date_start_1yr]
        n_years_1yr = (date_end - date_start_1yr).days / 365.25
        cagr_1yr = (val_end / val_start_1yr) ** (1 / n_years_1yr) - 1
    else:
        cagr_1yr = np.nan
        
    # 3 Year CAGR
    target_3yr = date_end - pd.DateOffset(years=3)
    available_3yr = fund_nav.index[fund_nav.index <= target_3yr]
    if len(available_3yr) > 0:
        date_start_3yr = available_3yr[-1]
        val_start_3yr = fund_nav.loc[date_start_3yr]
        n_years_3yr = (date_end - date_start_3yr).days / 365.25
        cagr_3yr = (val_end / val_start_3yr) ** (1 / n_years_3yr) - 1
    else:
        cagr_3yr = np.nan
        
    # 5 Year CAGR (proxy using maximum available history, ~4.4 years)
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
print("[2] Saved cagr_report.csv to reports/day4")

# 5. Compute Sharpe Ratio
rf_annual = 0.065
sharpe_results = []
vol_results = {}

for code in daily_returns.columns:
    returns = daily_returns[code].dropna()
    n = len(returns)
    if n == 0:
        continue
    
    mean_daily = returns.mean()
    std_daily = returns.std()
    
    rp_annual = mean_daily * 252
    vol_annual = std_daily * np.sqrt(252)
    vol_results[code] = vol_annual
    
    sharpe = (rp_annual - rf_annual) / vol_annual if vol_annual > 0 else np.nan
    
    sharpe_results.append({
        "amfi_code": code,
        "scheme_name": fund_names.get(code, "Unknown"),
        "rp_annualized_pct": rp_annual * 100,
        "vol_annualized_pct": vol_annual * 100,
        "sharpe_ratio": sharpe
    })

sharpe_df = pd.DataFrame(sharpe_results)
sharpe_df.to_csv(DAY4_REPORTS_DIR / "sharpe_values.csv", index=False)
print("[3] Saved sharpe_values.csv to reports/day4")

# 6. Compute Sortino Ratio
sortino_results = []

for code in daily_returns.columns:
    returns = daily_returns[code].dropna()
    n = len(returns)
    if n == 0:
        continue
        
    rp_annual = returns.mean() * 252
    
    negative_returns = returns[returns < 0]
    downside_std_daily = negative_returns.std()
    downside_std_annual = downside_std_daily * np.sqrt(252)
    
    sortino = (rp_annual - rf_annual) / downside_std_annual if downside_std_annual > 0 else np.nan
    
    sortino_results.append({
        "amfi_code": code,
        "scheme_name": fund_names.get(code, "Unknown"),
        "downside_std_annualized_pct": downside_std_annual * 100,
        "sortino_ratio": sortino
    })

sortino_df = pd.DataFrame(sortino_results)
sortino_df.to_csv(DAY4_REPORTS_DIR / "sortino_values.csv", index=False)
print("[4] Saved sortino_values.csv to reports/day4")

# 7. Compute Alpha & Beta vs benchmark (NIFTY100)
nifty100_df = bench_df[bench_df["index_name"] == "NIFTY100"].sort_values("date").copy()
nifty100_df["benchmark_return"] = nifty100_df["close_value"].pct_change()
nifty100_returns = nifty100_df.set_index("date")["benchmark_return"].dropna()

alpha_beta_results = []

for code in daily_returns.columns:
    fund_ret = daily_returns[code].dropna()
    merged = pd.concat([fund_ret, nifty100_returns], axis=1, join="inner")
    merged.columns = ["fund_ret", "bench_ret"]
    
    if len(merged) < 3:
        alpha_beta_results.append({
            "amfi_code": code,
            "scheme_name": fund_names.get(code, "Unknown"),
            "alpha": np.nan,
            "beta": np.nan
        })
        continue
        
    slope, intercept, _, _, _ = linregress(merged["bench_ret"], merged["fund_ret"])
    alpha = intercept * 252
    beta = slope
    
    alpha_beta_results.append({
        "amfi_code": code,
        "scheme_name": fund_names.get(code, "Unknown"),
        "alpha": alpha,
        "beta": beta
    })

alpha_beta_df = pd.DataFrame(alpha_beta_results)
alpha_beta_df.to_csv(DAY4_REPORTS_DIR / "alpha_beta.csv", index=False)
print("[5] Saved alpha_beta.csv to reports/day4")

# 8. Compute Maximum Drawdown
max_dd_results = []

for code in nav_pivot.columns:
    fund_nav = nav_pivot[code].dropna()
    if fund_nav.empty:
        continue
    
    running_max = fund_nav.cummax()
    drawdown = fund_nav / running_max - 1
    max_dd = drawdown.min()
    
    trough_idx = drawdown.idxmin()
    peak_idx = fund_nav.loc[:trough_idx].idxmax()
    
    post_trough = fund_nav.loc[trough_idx:]
    peak_value = fund_nav.loc[peak_idx]
    recovery_dates = post_trough[post_trough >= peak_value].index
    if len(recovery_dates) > 0:
        recovery_date = recovery_dates[0]
        recovery_days = (recovery_date - trough_idx).days
    else:
        recovery_date = "Not Recovered"
        recovery_days = np.nan
        
    max_dd_results.append({
        "amfi_code": code,
        "scheme_name": fund_names.get(code, "Unknown"),
        "max_drawdown_pct": max_dd * 100,
        "peak_date": peak_idx.strftime("%Y-%m-%d"),
        "trough_date": trough_idx.strftime("%Y-%m-%d"),
        "recovery_date": recovery_date if isinstance(recovery_date, str) else recovery_date.strftime("%Y-%m-%d"),
        "drawdown_days": (trough_idx - peak_idx).days,
        "recovery_days": recovery_days
    })

max_dd_df = pd.DataFrame(max_dd_results)
max_dd_df.to_csv(DAY4_REPORTS_DIR / "max_drawdown.csv", index=False)
print("[6] Saved max_drawdown.csv to reports/day4")

# 9. Build Fund Scorecard (composite score 0-100)
scorecard_base = pd.merge(cagr_report_df[["amfi_code", "scheme_name", "cagr_3yr_pct"]], sharpe_df[["amfi_code", "sharpe_ratio"]], on="amfi_code")
scorecard_base = pd.merge(scorecard_base, alpha_beta_df[["amfi_code", "alpha"]], on="amfi_code")
scorecard_base = pd.merge(scorecard_base, max_dd_df[["amfi_code", "max_drawdown_pct"]], on="amfi_code")
scorecard_base["expense_ratio_pct"] = scorecard_base["amfi_code"].map(fund_expenses)
scorecard_base["category"] = scorecard_base["amfi_code"].map(fund_categories)

clean_scorecard = scorecard_base.dropna(subset=["cagr_3yr_pct", "sharpe_ratio", "alpha", "expense_ratio_pct", "max_drawdown_pct"]).copy()

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
print("[7] Saved fund_scorecard.csv to reports/day4")

# 10. Generate Benchmark Chart and tracking error
top_5 = clean_scorecard.head(5)
top_5_codes = top_5["amfi_code"].tolist()

end_date_3yr = nav_df["date"].max()
start_date_3yr = end_date_3yr - pd.DateOffset(years=3)

nav_3yr = nav_df[(nav_df["date"] >= start_date_3yr) & (nav_df["date"] <= end_date_3yr)].copy()
bench_3yr = bench_df[(bench_df["date"] >= start_date_3yr) & (bench_df["date"] <= end_date_3yr)].copy()

nav_pivot_3yr = nav_3yr[nav_3yr["amfi_code"].isin(top_5_codes)].pivot(index="date", columns="amfi_code", values="nav").sort_index().ffill()
nav_normalized_3yr = nav_pivot_3yr.div(nav_pivot_3yr.iloc[0]) * 100

bench_pivot_3yr = bench_3yr.pivot(index="date", columns="index_name", values="close_value")
bench_pivot_3yr = bench_pivot_3yr[["NIFTY50", "NIFTY100"]].sort_index().ffill()
bench_normalized_3yr = bench_pivot_3yr.div(bench_pivot_3yr.iloc[0]) * 100

# Set plot style for premium aesthetic
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
fig.patch.set_facecolor('#fafafa')
ax.set_facecolor('#ffffff')

colors = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]

for i, code in enumerate(top_5_codes):
    name = top_5[top_5["amfi_code"] == code]["scheme_name"].values[0]
    short_name = name.split(" - ")[0]
    ax.plot(nav_normalized_3yr.index, nav_normalized_3yr[code], label=short_name, color=colors[i], linewidth=2.5, alpha=0.95)

ax.plot(bench_normalized_3yr.index, bench_normalized_3yr["NIFTY50"], label="NIFTY 50 (Benchmark)", color="#10B981", linestyle="--", linewidth=3, alpha=0.9)
ax.plot(bench_normalized_3yr.index, bench_normalized_3yr["NIFTY100"], label="NIFTY 100 (Benchmark)", color="#4B5563", linestyle="-.", linewidth=3, alpha=0.9)

ax.set_title("Top 5 Funds vs Benchmarks (3-Year Cumulative Indexed Returns)", fontsize=16, fontweight="bold", pad=20, color="#1e293b")
ax.set_xlabel("Date", fontsize=12, color="#475569", labelpad=12)
ax.set_ylabel("Indexed NAV (Base = 100)", fontsize=12, color="#475569", labelpad=12)
ax.tick_params(colors='#475569', labelsize=10)
ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=10)

plt.savefig(DAY4_REPORTS_DIR / "benchmark_comparison_chart.png", bbox_inches="tight", dpi=150)
plt.savefig(DAY4_REPORTS_DIR / "benchmark_chart.png", bbox_inches="tight", dpi=150)
plt.close()
print("[8] Saved benchmark charts to reports/day4")

# Calculate Tracking Errors
fund_returns_3yr = nav_pivot_3yr.pct_change().dropna()
nifty100_returns_3yr = bench_pivot_3yr["NIFTY100"].pct_change().dropna()

te_results = []
for code in top_5_codes:
    merged = pd.concat([fund_returns_3yr[code], nifty100_returns_3yr], axis=1, join="inner").dropna()
    merged.columns = ["fund", "bench"]
    diff = merged["fund"] - merged["bench"]
    te = diff.std() * np.sqrt(252)
    name = top_5[top_5["amfi_code"] == code]["scheme_name"].values[0]
    te_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "tracking_error_nifty100_pct": te * 100
    })
    print(f"Tracking Error for {name}: {te:.2%}")

te_df = pd.DataFrame(te_results)
te_df.to_csv(DAY4_REPORTS_DIR / "tracking_errors.csv", index=False)

# 11. Update SQLite database
if DB_PATH.exists():
    print("Updating bluestock_mf.db table: fact_performance...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We will update each fund in fact_performance with our newly computed values
    for index, row in clean_scorecard.iterrows():
        code = int(row["amfi_code"])
        cagr_1yr = float(cagr_report_df[cagr_report_df["amfi_code"] == code]["cagr_1yr_pct"].values[0])
        cagr_3yr = float(row["cagr_3yr_pct"])
        cagr_5yr = float(cagr_report_df[cagr_report_df["amfi_code"] == code]["cagr_5yr_pct"].values[0])
        alpha = float(row["alpha"])
        beta = float(alpha_beta_df[alpha_beta_df["amfi_code"] == code]["beta"].values[0])
        sharpe = float(row["sharpe_ratio"])
        sortino = float(sortino_df[sortino_df["amfi_code"] == code]["sortino_ratio"].values[0])
        std_dev = float(vol_results.get(code, np.nan) * 100)
        max_dd = float(row["max_drawdown_pct"])
        
        # Check if row exists, if not insert, otherwise update
        cursor.execute("SELECT 1 FROM fact_performance WHERE amfi_code = ?", (code,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE fact_performance
                SET return_1yr_pct = ?,
                    return_3yr_pct = ?,
                    return_5yr_pct = ?,
                    alpha = ?,
                    beta = ?,
                    sharpe_ratio = ?,
                    sortino_ratio = ?,
                    std_dev_ann_pct = ?,
                    max_drawdown_pct = ?
                WHERE amfi_code = ?
            """, (cagr_1yr, cagr_3yr, cagr_5yr, alpha, beta, sharpe, sortino, std_dev, max_dd, code))
        else:
            # Insert new record using fund master info
            fund_info = master_df[master_df["amfi_code"] == code].iloc[0]
            cursor.execute("""
                INSERT INTO fact_performance (
                    amfi_code, scheme_name, fund_house, category, variant_type,
                    return_1yr_pct, return_3yr_pct, return_5yr_pct,
                    alpha, beta, sharpe_ratio, sortino_ratio, std_dev_ann_pct, max_drawdown_pct,
                    aum_crore, expense_ratio_pct, risk_grade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, fund_info["scheme_name"], fund_info["fund_house"], fund_info["category"], fund_info["plan"],
                cagr_1yr, cagr_3yr, cagr_5yr, alpha, beta, sharpe, sortino, std_dev, max_dd,
                None, fund_info["expense_ratio_pct"], fund_info["risk_category"]
            ))
            
    conn.commit()
    conn.close()
    print("bluestock_mf.db successfully updated.")
else:
    print("bluestock_mf.db not found, skipping DB update.")

print("All analytics and reports completed successfully.")
