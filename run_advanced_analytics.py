import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Setup paths
BASE_DIR = Path("c:/repo/Mutual_Fund_Analysis")
REPORTS_DIR = BASE_DIR / "reports" / "day6"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

print("Starting Advanced Analytics & Risk Metrics (Day 6)...")

# Connect to database
conn = sqlite3.connect(DB_PATH)

# Load dataframes
dim_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
fact_nav = pd.read_sql_query("SELECT * FROM fact_nav", conn)
fact_transactions = pd.read_sql_query("SELECT * FROM fact_transactions", conn)
fact_holdings = pd.read_sql_query("SELECT * FROM fact_holdings", conn)

conn.close()

# 1. Compute Historical VaR (95%) and CVaR (95%) for each fund
print("[1] Calculating Value at Risk (VaR) & Conditional VaR (CVaR)...")
var_cvar_results = []
for code, group in fact_nav.groupby("amfi_code"):
    returns = group["daily_return"].dropna()
    if len(returns) == 0:
        continue
    
    # 5th percentile of return distribution
    var_95 = returns.quantile(0.05)
    
    # Mean of returns below VaR threshold
    cvar_95 = returns[returns <= var_95].mean()
    
    scheme_name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0]
    
    # We store VaR as a positive loss percentage and CVaR as a positive loss percentage
    var_cvar_results.append({
        "amfi_code": code,
        "scheme_name": scheme_name,
        "var_95_pct": -var_95 * 100,
        "cvar_95_pct": -cvar_95 * 100
    })

var_cvar_df = pd.DataFrame(var_cvar_results)
var_cvar_df.to_csv(REPORTS_DIR / "var_cvar_report.csv", index=False)
var_cvar_df.to_csv(BASE_DIR / "var_cvar_report.csv", index=False)
print("Saved var_cvar_report.csv")

# 2. Compute Rolling 90-day Sharpe Ratio for 5 funds
print("[2] Calculating Rolling 90-day Sharpe Ratio...")
# Let's pivot NAV to get returns
nav_pivot = fact_nav.pivot(index="nav_date", columns="amfi_code", values="daily_return").sort_index()

# Select 5 major funds (top 5 from scorecard)
selected_codes = [148567, 120505, 120843, 100033, 120504]
# Filter to existing codes in data
selected_codes = [c for c in selected_codes if c in nav_pivot.columns]

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
fig.patch.set_facecolor('#fafafa')
ax.set_facecolor('#ffffff')

COLORS = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]

for idx, code in enumerate(selected_codes):
    fund_returns = nav_pivot[code].dropna()
    rolling_mean = fund_returns.rolling(90).mean()
    rolling_std = fund_returns.rolling(90).std()
    rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
    
    name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0].split(" - ")[0]
    # Filter out initial NaNs
    rolling_sharpe = rolling_sharpe.dropna()
    dates = pd.to_datetime(rolling_sharpe.index)
    ax.plot(dates, rolling_sharpe, label=name, color=COLORS[idx % len(COLORS)], linewidth=2)

ax.set_title("Rolling 90-day Sharpe Ratio over Time (Top 5 Scorecard Funds)", fontsize=16, fontweight='bold', pad=20, color='#1e293b')
ax.set_xlabel("Date", fontsize=12, color='#475569', labelpad=12)
ax.set_ylabel("Rolling Sharpe Ratio (Annualized)", fontsize=12, color='#475569', labelpad=12)
ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=10)

plt.savefig(REPORTS_DIR / "rolling_sharpe_chart.png", bbox_inches="tight", facecolor='#fafafa')
plt.savefig(BASE_DIR / "rolling_sharpe_chart.png", bbox_inches="tight", facecolor='#fafafa')
plt.close()
print("Saved rolling_sharpe_chart.png")

# 3. Investor Cohort Analysis
print("[3] Performing Investor Cohort Analysis...")
# Cohort by first transaction date
fact_transactions["transaction_date"] = pd.to_datetime(fact_transactions["transaction_date"])
first_txn = fact_transactions.groupby("investor_id")["transaction_date"].min().reset_index()
first_txn.columns = ["investor_id", "first_txn_date"]
first_txn["cohort_year"] = first_txn["first_txn_date"].dt.year

# Merge back to transactions
tx_cohorts = fact_transactions.merge(first_txn[["investor_id", "cohort_year"]], on="investor_id")

# Analyze
cohort_results = []
for year, group in tx_cohorts.groupby("cohort_year"):
    # Total unique investors
    investor_count = group["investor_id"].nunique()
    
    # Average SIP amount
    sip_group = group[group["transaction_type"] == "SIP"]
    avg_sip = sip_group["amount_inr"].mean() if not sip_group.empty else 0.0
    
    # Total invested
    total_invested = group[group["transaction_type"] != "Redemption"]["amount_inr"].sum()
    
    # Fund category preference (by total transaction amount)
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
cohort_df.to_csv(REPORTS_DIR / "cohort_analysis.csv", index=False)
print("Saved cohort_analysis.csv")

# 4. SIP Continuation Analysis
print("[4] Performing SIP Continuation Analysis...")
sip_tx = fact_transactions[fact_transactions["transaction_type"] == "SIP"].copy()
sip_tx = sip_tx.sort_values(["investor_id", "transaction_date"])

continuity_results = []
for investor_id, group in sip_tx.groupby("investor_id"):
    txn_count = len(group)
    if txn_count < 6:
        continue
    
    # Compute gaps in days between consecutive SIPs
    dates = group["transaction_date"].sort_values()
    gaps = dates.diff().dropna().dt.days
    
    avg_gap = gaps.mean()
    max_gap = gaps.max()
    
    # Flag as 'at-risk' (gap > 35 days)
    at_risk = 1 if avg_gap > 35 else 0
    
    continuity_results.append({
        "investor_id": investor_id,
        "total_sip_transactions": txn_count,
        "avg_gap_days": avg_gap,
        "max_gap_days": max_gap,
        "at_risk_flag": at_risk
    })

continuity_df = pd.DataFrame(continuity_results)
continuity_df.to_csv(REPORTS_DIR / "sip_continuity.csv", index=False)
print("Saved sip_continuity.csv")

# 5. Sector Concentration Analysis (HHI)
print("[5] Performing Sector Concentration Analysis (HHI)...")
# Herfindahl-Hirschman Index (HHI) = sum(weight_i^2) of sector weights
hhi_results = []
# Group by amfi_code and sector
for code, group in fact_holdings.groupby("amfi_code"):
    scheme_name = dim_fund[dim_fund["amfi_code"] == code]["scheme_name"].values[0]
    cat = dim_fund[dim_fund["amfi_code"] == code]["category"].values[0]
    
    # Only analyze equity/hybrid funds
    if cat != "Equity":
        continue
        
    sector_weights = group.groupby("sector")["weight_pct"].sum()
    
    # Normalize weights to sum to 100
    if sector_weights.sum() > 0:
        norm_weights = sector_weights / sector_weights.sum() * 100
        hhi = np.sum(norm_weights ** 2)
    else:
        hhi = np.nan
        
    # Concentration flag
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
hhi_df.to_csv(REPORTS_DIR / "sector_hhi.csv", index=False)
print("Saved sector_hhi.csv")

# Plot HHI Bar Chart
fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
fig.patch.set_facecolor('#fafafa')
ax.set_facecolor('#ffffff')

# Top 15 funds by HHI for visualization
plot_hhi = hhi_df.head(15)
ax.bar(plot_hhi["scheme_name"].apply(lambda x: x.split(" - ")[0]), plot_hhi["sector_hhi"], color=COLORS[0], width=0.5)
ax.axhline(2500, color=COLORS[3], linestyle="--", label="Highly Concentrated Threshold (>2500)")
ax.axhline(1500, color=COLORS[4], linestyle="--", label="Moderately Concentrated Threshold (1500-2500)")

ax.set_title("Sector Concentration Risk (Herfindahl-Hirschman Index - HHI)", fontsize=14, fontweight='bold', pad=15, color='#1e293b')
ax.set_xlabel("Scheme Name", fontsize=10, color='#475569', labelpad=12)
ax.set_ylabel("Sector HHI Score", fontsize=10, color='#475569', labelpad=12)
ax.tick_params(axis='x', rotation=30, labelsize=8)
ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=9)

plt.savefig(REPORTS_DIR / "sector_hhi_chart.png", bbox_inches="tight", facecolor='#fafafa')
plt.close()
print("Saved sector_hhi_chart.png")

print("All advanced calculations completed successfully.")
