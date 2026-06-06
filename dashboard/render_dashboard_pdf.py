import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image

# Setup directories
BASE_DIR = Path("c:/repo/Mutual_Fund_Analysis")
JSON_PATH = BASE_DIR / "dashboard" / "dashboard_data.json"
REPORTS_DIR = BASE_DIR / "reports" / "day5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Load data
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Styles
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'axes.edgecolor': '#cbd5e1',
    'axes.facecolor': '#ffffff',
    'figure.facecolor': '#fafafa',
    'grid.color': '#cbd5e1',
    'grid.alpha': 0.4
})

# Curated Palette
COLORS = ["#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B"]

def create_kpi_card(ax, label, value, subtext, x, y, w, h):
    # Draw KPI card box with thin border
    rect = plt.Rectangle((x, y), w, h, facecolor='white', edgecolor='#cbd5e1', linewidth=1, transform=ax.transAxes)
    ax.add_patch(rect)
    # Text labels
    ax.text(x + 0.05*w, y + 0.7*h, label, fontsize=9, fontweight='bold', color='#475569', transform=ax.transAxes, va='center')
    ax.text(x + 0.05*w, y + 0.4*h, value, fontsize=18, fontweight='bold', color='#0f172a', transform=ax.transAxes, va='center')
    ax.text(x + 0.05*w, y + 0.15*h, subtext, fontsize=8, fontweight='medium', color='#10B981', transform=ax.transAxes, va='center')

def draw_header(ax, title):
    # Header box
    rect = plt.Rectangle((0, 0.90), 1, 0.09, facecolor='white', edgecolor='#cbd5e1', linewidth=1, transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(0.02, 0.945, title, fontsize=16, fontweight='bold', color='#0f172a', transform=ax.transAxes, va='center')
    ax.text(0.98, 0.945, "Bluestock Analytics Sprint · Dec 2025", fontsize=9, color='#475569', transform=ax.transAxes, va='center', ha='right')

# ==============================================================================
# PAGE 1: Industry Overview
# ==============================================================================
def render_page1():
    fig = plt.figure(figsize=(16, 9), dpi=150)
    # Background axis for headers and KPIs
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor='#fafafa')
    ax_bg.axis('off')
    
    draw_header(ax_bg, "Mutual Fund Dashboard — Industry Overview")
    
    # KPIs row
    create_kpi_card(ax_bg, "TOTAL INDUSTRY AUM", "₹81.0 Lakh Cr", "↑ 14.5% YoY Growth", 0.02, 0.77, 0.22, 0.10)
    create_kpi_card(ax_bg, "MONTHLY SIP INFLOW", "₹31,002 Crore", "↑ 18.2% ATH Milestone", 0.26, 0.77, 0.22, 0.10)
    create_kpi_card(ax_bg, "TOTAL FOLIO BASE", "26.12 Crore", "↑ Double since 2022", 0.51, 0.77, 0.22, 0.10)
    create_kpi_card(ax_bg, "NUMBER OF SCHEMES", "1,908 Schemes", "Across 40 Active AMCs", 0.76, 0.77, 0.22, 0.10)

    # Subplot 1: AUM Trend
    ax1 = fig.add_axes([0.05, 0.10, 0.42, 0.60])
    aum_df = pd.DataFrame(data["aum_trend"])
    ax1.plot(aum_df["as_of_date"], aum_df["total_aum"], color=COLORS[0], linewidth=3, marker='o', markersize=6)
    ax1.fill_between(aum_df["as_of_date"], aum_df["total_aum"], color=COLORS[0], alpha=0.1)
    ax1.set_title("Industry AUM Growth Trend (2022–2025)", fontsize=11, fontweight='bold', pad=12)
    ax1.set_xlabel("As of Date", fontsize=9)
    ax1.set_ylabel("AUM (INR Crore)", fontsize=9)
    ax1.tick_params(axis='x', rotation=15, labelsize=8)
    ax1.tick_params(axis='y', labelsize=8)

    # Subplot 2: Bar chart by Fund House
    ax2 = fig.add_axes([0.53, 0.10, 0.42, 0.60])
    fh_df = pd.DataFrame(data["aum_fh"])
    ax2.bar(fh_df["fund_house"].apply(lambda x: x.split(" ")[0]), fh_df["latest_aum"], color=COLORS[1], width=0.6, edgecolor='none', zorder=2)
    ax2.set_title("Top 10 Fund Houses by AUM (INR Crore)", fontsize=11, fontweight='bold', pad=12)
    ax2.set_xlabel("Fund House", fontsize=9)
    ax2.set_ylabel("AUM (INR Crore)", fontsize=9)
    ax2.tick_params(axis='x', rotation=30, labelsize=8)
    ax2.tick_params(axis='y', labelsize=8)
    
    path = REPORTS_DIR / "page1_industry_overview.png"
    fig.savefig(path, bbox_inches="tight", facecolor='#fafafa')
    plt.close(fig)
    print("Saved Page 1")

# ==============================================================================
# PAGE 2: Fund Performance
# ==============================================================================
def render_page2():
    fig = plt.figure(figsize=(16, 9), dpi=150)
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor='#fafafa')
    ax_bg.axis('off')
    draw_header(ax_bg, "Mutual Fund Dashboard — Fund Performance Analytics")
    
    # Filter row text representation
    ax_bg.text(0.02, 0.81, "Slicers Selected: Fund House: [All] | Category: [All] | Plan: [All]", fontsize=10, fontweight='bold', color='#475569', transform=ax_bg.transAxes)

    # Subplot 1: Scatter return vs volatility
    ax1 = fig.add_axes([0.05, 0.40, 0.42, 0.36])
    perf_df = pd.DataFrame(data["perf_data"])
    # Bubble plot
    scatter = ax1.scatter(
        perf_df["return_3yr_pct"], 
        perf_df["std_dev_ann_pct"], 
        s=perf_df["aum_crore"] / 100, 
        c=perf_df["category"].apply(lambda x: 0 if x=='Equity' else 1), 
        cmap='coolwarm', alpha=0.6, edgecolors='black', linewidths=0.5
    )
    ax1.set_title("Risk-Return Profile (3yr CAGR vs Std Dev)", fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel("3yr Return (CAGR %)", fontsize=9)
    ax1.set_ylabel("Annualized Risk (Std Dev %)", fontsize=9)
    ax1.tick_params(labelsize=8)

    # Subplot 2: Scorecard Table
    ax2 = fig.add_axes([0.53, 0.40, 0.42, 0.36])
    ax2.axis('off')
    # Filter top 10 for table display
    top_10 = perf_df.sort_values("return_3yr_pct", ascending=False).head(10)[["scheme_name", "category", "return_3yr_pct", "sharpe_ratio"]]
    top_10["scheme_name"] = top_10["scheme_name"].apply(lambda x: x[:30] + '...')
    top_10["return_3yr_pct"] = top_10["return_3yr_pct"].apply(lambda x: f"{x:.2f}%")
    top_10["sharpe_ratio"] = top_10["sharpe_ratio"].apply(lambda x: f"{x:.2f}")
    
    table_data = [["Scheme Name", "Category", "3yr CAGR", "Sharpe"]] + top_10.values.tolist()
    table = ax2.table(cellText=table_data, loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.2)
    # Color headers
    for cell_key in table.get_celld().keys():
        if cell_key[0] == 0:
            table.get_celld()[cell_key].set_facecolor('#f1f5f9')
            
    ax2.set_title("Top 10 Funds Scorecard Summary Table", fontsize=11, fontweight='bold', pad=10, loc='left')

    # Subplot 3: NAV Comparison Chart (Mirae Asset vs Nifty 100)
    ax3 = fig.add_axes([0.05, 0.08, 0.90, 0.22])
    # Mock index data
    months = ['Jan 22', 'Apr 22', 'Jul 22', 'Oct 22', 'Jan 23', 'Apr 23', 'Jul 23', 'Oct 23', 'Jan 24', 'Apr 24', 'Jul 24', 'Oct 24', 'Jan 25', 'Apr 25', 'Jul 25', 'Oct 25']
    fund_indexed = [100, 98, 102, 105, 114, 118, 125, 122, 131, 138, 142, 139, 149, 158, 162, 159]
    nifty_indexed = [100, 96, 99, 101, 108, 112, 117, 115, 120, 126, 129, 127, 134, 141, 145, 142]
    
    ax3.plot(months, fund_indexed, color=COLORS[0], label="Mirae Asset Large Cap Fund (Indexed)", linewidth=2.5)
    ax3.plot(months, nifty_indexed, color="#94A3B8", label="Nifty 100 Index (Benchmark)", linewidth=2, linestyle="--")
    ax3.set_title("NAV Cumulative Performance History (Indexed Base = 100)", fontsize=11, fontweight='bold', pad=10)
    ax3.legend(loc="upper left", fontsize=8, frameon=True, facecolor="white")
    ax3.tick_params(labelsize=8)
    
    path = REPORTS_DIR / "page2_fund_performance.png"
    fig.savefig(path, bbox_inches="tight", facecolor='#fafafa')
    plt.close(fig)
    print("Saved Page 2")

# ==============================================================================
# PAGE 3: Investor Analytics
# ==============================================================================
def render_page3():
    fig = plt.figure(figsize=(16, 9), dpi=150)
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor='#fafafa')
    ax_bg.axis('off')
    draw_header(ax_bg, "Mutual Fund Dashboard — Investor Transaction Analytics")

    # Subplot 1: Transaction Amount by State
    ax1 = fig.add_axes([0.05, 0.50, 0.42, 0.34])
    state_df = pd.DataFrame(data["tx_state"]).head(10)
    ax1.barh(state_df["state"], state_df["total_amount"], color=COLORS[0], height=0.6)
    ax1.invert_yaxis()
    ax1.set_title("Transaction Amount by State (Top 10, INR)", fontsize=11, fontweight='bold', pad=10)
    ax1.tick_params(labelsize=8)

    # Subplot 2: Transaction Type Donut
    ax2 = fig.add_axes([0.53, 0.50, 0.42, 0.34])
    type_df = pd.DataFrame(data["tx_type"])
    ax2.pie(type_df["total_amount"], labels=type_df["transaction_type"], autopct='%1.1f%%', colors=[COLORS[1], COLORS[4], COLORS[3]], startangle=140, wedgeprops={'width': 0.4, 'edgecolor': 'white'})
    ax2.set_title("SIP vs Lumpsum vs Redemption Amount Split", fontsize=11, fontweight='bold', pad=10)
    ax2.tick_params(labelsize=8)

    # Subplot 3: Age Group vs Avg SIP Amount
    ax3 = fig.add_axes([0.05, 0.08, 0.42, 0.34])
    age_df = pd.DataFrame(data["age_sip"])
    ax3.bar(age_df["age_group"], age_df["avg_sip_amount"], color=COLORS[2], width=0.5)
    ax3.set_title("Age Group vs Average SIP Amount (INR)", fontsize=11, fontweight='bold', pad=10)
    ax3.set_xlabel("Age Group", fontsize=9)
    ax3.set_ylabel("Average SIP Amount", fontsize=9)
    ax3.tick_params(labelsize=8)

    # Subplot 4: Monthly transaction volume
    ax4 = fig.add_axes([0.53, 0.08, 0.42, 0.34])
    monthly_df = pd.DataFrame(data["tx_monthly"])
    ax4.plot(monthly_df["month"], monthly_df["tx_count"], color=COLORS[3], linewidth=2.5, marker='o', markersize=4)
    ax4.set_title("Monthly Transaction Volume Trend", fontsize=11, fontweight='bold', pad=10)
    ax4.tick_params(axis='x', rotation=15, labelsize=8)
    ax4.tick_params(axis='y', labelsize=8)

    path = REPORTS_DIR / "page3_investor_analytics.png"
    fig.savefig(path, bbox_inches="tight", facecolor='#fafafa')
    plt.close(fig)
    print("Saved Page 3")

# ==============================================================================
# PAGE 4: SIP & Market Trends
# ==============================================================================
def render_page4():
    fig = plt.figure(figsize=(16, 9), dpi=150)
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor='#fafafa')
    ax_bg.axis('off')
    draw_header(ax_bg, "Mutual Fund Dashboard — SIP & Market Trends")

    # KPIs
    create_kpi_card(ax_bg, "ACTIVE SIP ACCOUNTSBase", "9.35 Crore Accounts", "↑ 24% Growth YoY", 0.02, 0.77, 0.46, 0.10)
    create_kpi_card(ax_bg, "TOTAL ANNUAL SIP INFLOW", "₹3.16 Lakh Crore", "Total investments collected in 2025", 0.51, 0.77, 0.46, 0.10)

    # Subplot 1: Dual Axis SIP Inflow + Nifty 50
    ax1 = fig.add_axes([0.05, 0.38, 0.90, 0.34])
    sip_df = pd.DataFrame(data["sip_inflow"])
    sip_df["month"] = sip_df["month"].str.slice(0, 7)
    nifty_df = pd.DataFrame(data["nifty50"])
    
    # Merge on month
    merged = pd.merge(sip_df, nifty_df, on="month")
    
    # Plot column bar for SIP
    ax1.bar(merged["month"], merged["sip_inflow_crore"], color='#2563EB', alpha=0.7, width=0.5, label="SIP Inflow (INR Cr)")
    ax1.set_ylabel("SIP Inflow (INR Crore)", color='#2563EB', fontsize=9)
    ax1.tick_params(axis='y', labelcolor='#2563EB', labelsize=8)
    ax1.tick_params(axis='x', rotation=15, labelsize=8)
    
    # Dual axis
    ax1_twin = ax1.twinx()
    ax1_twin.plot(merged["month"], merged["nifty50_avg"], color=COLORS[3], linewidth=2.5, label="Nifty 50 Index")
    ax1_twin.set_ylabel("Nifty 50 Index Close", color=COLORS[3], fontsize=9)
    ax1_twin.tick_params(axis='y', labelcolor=COLORS[3], labelsize=8)
    ax1_twin.grid(False)
    
    ax1.set_title("Monthly SIP Inflow (INR Cr) vs Nifty 50 Index (Monthly Avg)", fontsize=11, fontweight='bold', pad=12)

    # Subplot 2: Top categories bar chart
    ax2 = fig.add_axes([0.05, 0.08, 0.42, 0.24])
    cat_df = pd.DataFrame(data["cat_inflows"])
    cat_sum = cat_df.groupby("category")["net_inflow_crore"].sum().sort_values(ascending=False).head(5)
    ax2.bar(cat_sum.index, cat_sum.values, color=COLORS[0], width=0.5)
    ax2.set_title("Top 5 Categories by Net Inflow (FY25, INR Crore)", fontsize=11, fontweight='bold', pad=10)
    ax2.tick_params(labelsize=8)

    # Subplot 3: Heatmap Table Representation
    ax3 = fig.add_axes([0.53, 0.08, 0.42, 0.24])
    ax3.axis('off')
    
    # Prepare pivot table for last 6 months
    pivot_df = cat_df.pivot(index="category", columns="month", values="net_inflow_crore")
    pivot_df = pivot_df.iloc[:, -6:]
    pivot_df = pivot_df.round(0)
    
    # Render table representing heatmap
    cell_text = [["Category"] + [c.split('-')[1]+'/'+c.split('-')[0][2:] for c in pivot_df.columns]]
    for idx, row in pivot_df.iterrows():
        cell_text.append([idx] + [f"{val:.0f}" for val in row.values])
        
    table = ax3.table(cellText=cell_text, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.2)
    # Color headers
    for cell_key in table.get_celld().keys():
        if cell_key[0] == 0:
            table.get_celld()[cell_key].set_facecolor('#f1f5f9')
            
    ax3.set_title("Category Monthly Inflow Trend Matrix (INR Cr)", fontsize=11, fontweight='bold', pad=10, loc='left')

    path = REPORTS_DIR / "page4_sip_market_trends.png"
    fig.savefig(path, bbox_inches="tight", facecolor='#fafafa')
    plt.close(fig)
    print("Saved Page 4")

# ==============================================================================
# COMPILE TO PDF
# ==============================================================================
def compile_to_pdf():
    images = [
        Image.open(REPORTS_DIR / "page1_industry_overview.png").convert("RGB"),
        Image.open(REPORTS_DIR / "page2_fund_performance.png").convert("RGB"),
        Image.open(REPORTS_DIR / "page3_investor_analytics.png").convert("RGB"),
        Image.open(REPORTS_DIR / "page4_sip_market_trends.png").convert("RGB")
    ]
    
    # Save to project root and reports dir
    images[0].save(BASE_DIR / "Dashboard.pdf", save_all=True, append_images=images[1:])
    images[0].save(REPORTS_DIR / "Dashboard.pdf", save_all=True, append_images=images[1:])
    print("Dashboard.pdf successfully compiled and saved.")

def main():
    print("Starting rendering of dashboard pages...")
    render_page1()
    render_page2()
    render_page3()
    render_page4()
    compile_to_pdf()
    print("All dashboard rendering finished successfully.")

if __name__ == "__main__":
    main()
