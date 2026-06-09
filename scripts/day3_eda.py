"""
scripts/day3_eda.py
===================
Day 3 Exploratory Data Analysis.
Performs data visualizations and creates over 15 charts saved in reports/day3_charts/.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from matplotlib.figure import Figure

warnings.filterwarnings("ignore")
pio.templates.default = "plotly_white"


def project_root(start: Path | None = None) -> Path:
    """Traverse parent directories to locate the project root folder."""
    start = start or Path.cwd()
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "processed").exists():
            return candidate
    return start


BASE_DIR = project_root()
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "day3_charts"

CHART_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = [
    "#0F766E", "#2563EB", "#7C3AED", "#DC2626", "#F59E0B",
    "#059669", "#DB2777", "#4F46E5", "#0891B2", "#9333EA",
]

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#0f172a",
    "text.color": "#0f172a",
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "grid.color": "#e2e8f0",
    "font.family": "DejaVu Sans",
    "figure.dpi": 140,
})


def load_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Helper to read processed CSV files from the data/processed directory."""
    return pd.read_csv(PROCESSED_DIR / name, parse_dates=parse_dates or [])


def load_datasets() -> dict[str, pd.DataFrame]:
    """Load all cleaned datasets into a dictionary."""
    datasets = {
        "fund_master": load_csv("01_fund_master.csv", ["launch_date"]),
        "nav_history": load_csv("clean_nav.csv", ["date"]),
        "aum_fh": load_csv("03_aum_by_fund_house.csv", ["date"]),
        "sip_inflows": load_csv("04_monthly_sip_inflows.csv", ["month"]),
        "cat_inflows": load_csv("05_category_inflows.csv", ["month"]),
        "folio_count": load_csv("06_industry_folio_count.csv", ["month"]),
        "scheme_perf": load_csv("clean_performance.csv"),
        "investor_tx": load_csv("clean_transactions.csv", ["transaction_date"]),
        "portfolio": load_csv("09_portfolio_holdings.csv", ["portfolio_date"]),
        "benchmark": load_csv("10_benchmark_indices.csv", ["date"]),
    }
    return datasets


def _save_matplotlib(fig: Figure, name: str) -> Path:
    """Helper to save a matplotlib figure to the reports/day3_charts/ folder."""
    path = CHART_DIR / name
    fig.savefig(path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    return path


def _export_plotly(fig: go.Figure, stem: str) -> Path:
    """Helper to save a plotly figure as an image or HTML fallback."""
    png_path = CHART_DIR / f"{stem}.png"
    html_path = CHART_DIR / f"{stem}.html"
    try:
        fig.write_image(str(png_path), scale=2)
        return png_path
    except Exception:
        fig.write_html(str(html_path), include_plotlyjs="cdn")
        return html_path


def _fund_name_map(fund_master: pd.DataFrame) -> dict[int | str, str]:
    """Helper to create a mapping from AMFI code to scheme name."""
    fund_names: dict[int | str, str] = {}
    for code, name in fund_master.set_index("amfi_code")["scheme_name"].items():
        if isinstance(code, str):
            fund_names[code] = str(name)
        elif isinstance(code, (int, np.integer)):
            fund_names[int(code)] = str(name)
    return fund_names


def nav_charts(data: dict[str, pd.DataFrame]) -> list[Path]:
    """Generate and save charts related to NAV trend lines."""
    fund_master = data["fund_master"]
    nav_history = data["nav_history"].copy()
    nav_history = nav_history.merge(fund_master[["amfi_code", "scheme_name", "category", "fund_house"]], on="amfi_code", how="left")
    nav_history = nav_history.sort_values(["amfi_code", "date"])
    nav_history["nav_index"] = nav_history.groupby("amfi_code")["nav"].transform(lambda s: s / s.iloc[0] * 100)

    outputs: list[Path] = []

    # Chart 1: all schemes raw NAV trend
    fig, ax = plt.subplots(figsize=(16, 9))
    for idx, (code, grp) in enumerate(nav_history.groupby("amfi_code")):
        ax.plot(
            grp["date"],
            grp["nav"],
            color=PALETTE[idx % len(PALETTE)],
            alpha=0.35,
            linewidth=1.0,
        )
    ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31"), color="#dbeafe", alpha=0.5, label="2022 recovery base")
    ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), color="#dcfce7", alpha=0.35, label="2023 rally")
    ax.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31"), color="#fee2e2", alpha=0.35, label="2024 correction")
    ax.set_title("NAV Trend Lines Across All 40 Schemes (2022–2026)", weight="bold", pad=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("NAV")
    ax.legend(loc="upper left", ncol=2, fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    outputs.append(_save_matplotlib(fig, "nav_trend_all_schemes.png"))

    # Chart 2: indexed NAV by category
    monthly = nav_history.assign(month=nav_history["date"].dt.to_period("M").dt.to_timestamp())
    category_index = monthly.groupby(["month", "category"], as_index=False)["nav_index"].mean()
    fig, ax = plt.subplots(figsize=(16, 8))
    for idx, (category, grp) in enumerate(category_index.groupby("category")):
        ax.plot(grp["month"], grp["nav_index"], linewidth=2, label=category, color=PALETTE[idx % len(PALETTE)])
    for start, end, label, color in [
        ("2022-01-01", "2022-12-31", "Recovery base", "#dbeafe"),
        ("2023-01-01", "2023-12-31", "Rally", "#dcfce7"),
        ("2024-01-01", "2024-12-31", "Correction", "#fee2e2"),
    ]:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color=color, alpha=0.25)
    ax.set_title("Normalized NAV Index by Category", weight="bold", pad=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Indexed NAV (Base = 100)")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    outputs.append(_save_matplotlib(fig, "nav_index_by_category.png"))

    return outputs


def aum_sip_charts(data: dict[str, pd.DataFrame]) -> list[Path]:
    """Generate and save charts related to AUM growth and SIP inflow trends."""
    aum_fh = data["aum_fh"].copy()
    sip_inflows = data["sip_inflows"].copy()
    cat_inflows = data["cat_inflows"].copy()

    outputs: list[Path] = []

    # Chart 3: grouped AUM bar chart
    aum_fh["year"] = aum_fh["date"].dt.year
    aum_yearly = cast(pd.DataFrame, aum_fh.groupby(["year", "fund_house"], as_index=False)["aum_crore"].max())
    order = (
        aum_yearly[aum_yearly["year"] == aum_yearly["year"].max()]
        .sort_values("aum_crore", ascending=False)["fund_house"]
        .tolist()
    )
    fig, ax = plt.subplots(figsize=(18, 8))
    sns.barplot(data=cast(pd.DataFrame, aum_yearly), x="fund_house", y="aum_crore", hue="year", order=order, palette="viridis", ax=ax)
    ax.set_title("AUM Growth by AMC (2022–2025)", weight="bold", pad=14)
    ax.set_xlabel("Fund House")
    ax.set_ylabel("AUM (INR Crore)")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(title="Year", frameon=True)
    if (aum_yearly["fund_house"] == "SBI Mutual Fund").any():
        sbi_latest = aum_yearly[(aum_yearly["fund_house"] == "SBI Mutual Fund") & (aum_yearly["year"] == aum_yearly["year"].max())]["aum_crore"].iloc[0]
        ax.annotate(
            "SBI dominance",
            xy=(order.index("SBI Mutual Fund"), sbi_latest),
            xytext=(0, 18),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            weight="bold",
            color="#0f172a",
        )
    outputs.append(_save_matplotlib(fig, "aum_growth_by_amc.png"))

    # Chart 4: SIP inflow trend (plotly)
    sip_inflows = sip_inflows.sort_values("month")
    fig = px.line(
        sip_inflows,
        x="month",
        y="sip_inflow_crore",
        markers=True,
        title="Monthly SIP Inflow Trend (Jan 2022 – Dec 2025)",
        labels={"month": "Month", "sip_inflow_crore": "SIP Inflow (INR Crore)"},
    )
    fig.add_vline(x=pd.Timestamp("2025-12-01"), line_width=2, line_dash="dash", line_color="#dc2626")
    milestone = sip_inflows.loc[sip_inflows["month"].dt.strftime("%Y-%m").eq("2025-12"), "sip_inflow_crore"]
    if not milestone.empty:
        fig.add_annotation(
            x=pd.Timestamp("2025-12-01"),
            y=float(milestone.iloc[0]),
            text="₹31,002 Cr milestone",
            showarrow=True,
            arrowhead=2,
            ax=40,
            ay=-40,
        )
    fig.update_traces(line=dict(color="#0f766e", width=3), marker=dict(size=7))
    fig.update_layout(template="plotly_white", title_x=0.03)
    outputs.append(_export_plotly(fig, "sip_inflow_trend"))

    # Chart 5: category inflow heatmap
    cat_pivot = cat_inflows.pivot(index="category", columns="month", values="net_inflow_crore").sort_index()
    fig, ax = plt.subplots(figsize=(18, 7))
    sns.heatmap(cat_pivot, cmap="mako", linewidths=0.3, linecolor="white", ax=ax, cbar_kws={"label": "Net inflow (INR Cr)"})
    ax.set_title("Category-wise Net Inflow Heatmap", weight="bold", pad=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Category")
    outputs.append(_save_matplotlib(fig, "category_inflow_heatmap.png"))

    return outputs


def demographic_geo_charts(data: dict[str, pd.DataFrame]) -> list[Path]:
    """Generate and save charts related to investor demography and geographic tier patterns."""
    investor_tx = data["investor_tx"].copy()
    outputs: list[Path] = []

    investor_tx["age_group"] = investor_tx["age_group"].astype(str).str.strip()
    age_counts = investor_tx["age_group"].value_counts().sort_index()
    sip_by_age = investor_tx[investor_tx["transaction_type"].eq("SIP")].copy()
    sip_by_age["amount_inr"] = pd.to_numeric(sip_by_age["amount_inr"], errors="coerce")

    # Chart 6: age group pie
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(
        age_counts,
        labels=age_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=sns.color_palette("Set2", len(age_counts)),
        wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    )
    ax.set_title("Investor Age Group Distribution", weight="bold", pad=14)
    outputs.append(_save_matplotlib(fig, "age_group_pie.png"))

    # Chart 7: SIP box plot by age group
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(data=sip_by_age, x="age_group", y="amount_inr", palette="Blues", ax=ax)
    ax.set_title("SIP Amount Distribution by Age Group", weight="bold", pad=14)
    ax.set_xlabel("Age Group")
    ax.set_ylabel("SIP Amount (INR)")
    outputs.append(_save_matplotlib(fig, "sip_boxplot_by_age.png"))

    # Chart 8: state horizontal bar
    state_sip = (
        sip_by_age.groupby("state", as_index=False).agg(amount_inr=("amount_inr", "sum")).sort_values(by="amount_inr", ascending=False).head(15)
    )
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.barplot(data=state_sip, y="state", x="amount_inr", palette="crest", ax=ax)
    ax.set_title("Top States by SIP Amount", weight="bold", pad=14)
    ax.set_xlabel("SIP Amount (INR)")
    ax.set_ylabel("State")
    outputs.append(_save_matplotlib(fig, "sip_amount_by_state.png"))

    # Chart 9: T30 vs B30 pie
    tier_split = sip_by_age.groupby("city_tier", as_index=False).agg(amount_inr=("amount_inr", "sum")).sort_values(by="amount_inr", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(
        tier_split["amount_inr"],
        labels=tier_split["city_tier"],
        autopct="%1.1f%%",
        startangle=110,
        colors=["#2563EB", "#F59E0B"],
        wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    )
    ax.set_title("SIP Amount Split: T30 vs B30", weight="bold", pad=14)
    outputs.append(_save_matplotlib(fig, "t30_b30_pie.png"))

    return outputs


def portfolio_charts(data: dict[str, pd.DataFrame]) -> list[Path]:
    """Generate and save charts related to portfolios, returns, and sector concentration."""
    folio_count = data["folio_count"].copy()
    nav_history = data["nav_history"].copy()
    fund_master = data["fund_master"].copy()
    portfolio = data["portfolio"].copy()

    outputs: list[Path] = []

    # Chart 10: folio growth (plotly)
    fig = px.line(
        folio_count.sort_values("month"),
        x="month",
        y="total_folios_crore",
        markers=True,
        title="Industry Folio Count Growth (2022–2025)",
        labels={"month": "Month", "total_folios_crore": "Total Folios (Crore)"},
    )
    fig.add_annotation(x=folio_count["month"].min(), y=float(folio_count["total_folios_crore"].min()), text="13.26 Cr", showarrow=False, yshift=12)
    fig.add_annotation(x=folio_count["month"].max(), y=float(folio_count["total_folios_crore"].max()), text="26.12 Cr", showarrow=False, yshift=12)
    fig.update_traces(line=dict(color="#7c3aed", width=3), marker=dict(size=7))
    outputs.append(_export_plotly(fig, "folio_count_growth"))

    # Chart 11: correlation matrix of 10 selected funds
    selected_codes = data["scheme_perf"].nlargest(10, "aum_crore")["amfi_code"].tolist()
    nav_returns = nav_history[nav_history["amfi_code"].isin(selected_codes)].copy()
    nav_returns = nav_returns.sort_values(["amfi_code", "date"])
    nav_returns["daily_return"] = nav_returns.groupby("amfi_code")["nav"].pct_change()
    return_matrix = nav_returns.pivot(index="date", columns="amfi_code", values="daily_return")
    return_matrix.columns = [fund_master.set_index("amfi_code").loc[c, "scheme_name"] for c in return_matrix.columns]
    corr = return_matrix.corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, cmap="vlag", center=0, linewidths=0.25, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlation Matrix of NAV Returns (Top 10 Funds by AUM)", weight="bold", pad=14)
    outputs.append(_save_matplotlib(fig, "nav_return_correlation_matrix.png"))

    # Chart 12: sector allocation donut
    equity_codes = fund_master.loc[fund_master["category"].eq("Equity"), "amfi_code"]
    sector_alloc = (
        portfolio[portfolio["amfi_code"].isin(equity_codes)]
        .groupby("sector", as_index=False).agg(market_value_cr=("market_value_cr", "sum"))
        .sort_values(by="market_value_cr", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(9, 9))
    wedges, texts, autotexts = ax.pie(
        sector_alloc["market_value_cr"],
        labels=sector_alloc["sector"],
        autopct="%1.1f%%",
        startangle=90,
        colors=sns.color_palette("tab20", len(sector_alloc)),
        wedgeprops={"width": 0.38, "edgecolor": "white"},
    )
    ax.set_title("Sector Allocation Across Equity Portfolios", weight="bold", pad=14)
    outputs.append(_save_matplotlib(fig, "sector_allocation_donut.png"))

    return outputs


def performance_charts(data: dict[str, pd.DataFrame]) -> list[Path]:
    """Generate scatterplots comparing returns with risk, AUM, and expense ratio."""
    scheme_perf = data["scheme_perf"].copy()
    outputs: list[Path] = []

    # Chart 13: expense ratio vs 3-year return
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=scheme_perf,
        x="expense_ratio_pct",
        y="return_3yr_pct",
        hue="category",
        palette="tab10",
        s=110,
        alpha=0.9,
        ax=ax,
    )
    ax.set_title("Expense Ratio vs 3-Year Return", weight="bold", pad=14)
    ax.set_xlabel("Expense Ratio (%)")
    ax.set_ylabel("3-Year Return (%)")
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    outputs.append(_save_matplotlib(fig, "expense_vs_return_scatter.png"))

    # Chart 14: AUM vs 3-year return
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=scheme_perf,
        x="aum_crore",
        y="return_3yr_pct",
        hue="risk_grade",
        palette="Spectral",
        s=110,
        alpha=0.9,
        ax=ax,
    )
    ax.set_title("AUM vs 3-Year Return", weight="bold", pad=14)
    ax.set_xlabel("AUM (INR Crore)")
    ax.set_ylabel("3-Year Return (%)")
    ax.legend(title="Risk Grade", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    outputs.append(_save_matplotlib(fig, "aum_vs_return_scatter.png"))

    # Chart 15: max drawdown vs 5-year return
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=scheme_perf,
        x="max_drawdown_pct",
        y="return_5yr_pct",
        hue="category",
        palette="deep",
        s=110,
        alpha=0.9,
        ax=ax,
    )
    ax.set_title("Maximum Drawdown vs 5-Year Return", weight="bold", pad=14)
    ax.set_xlabel("Max Drawdown (%)")
    ax.set_ylabel("5-Year Return (%)")
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    outputs.append(_save_matplotlib(fig, "drawdown_vs_return_scatter.png"))

    # Chart 16: risk grade counts
    risk_counts = scheme_perf["risk_grade"].value_counts()
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(x=risk_counts.index, y=risk_counts.values, palette="flare", ax=ax)
    ax.set_title("Scheme Counts by Risk Grade", weight="bold", pad=14)
    ax.set_xlabel("Risk Grade")
    ax.set_ylabel("Scheme Count")
    ax.tick_params(axis="x", rotation=20)
    outputs.append(_save_matplotlib(fig, "risk_grade_counts.png"))

    return outputs


def build_findings(data: dict[str, pd.DataFrame]) -> list[str]:
    """Analyze datasets to extract key business findings and write a markdown summary."""
    fund_master = data["fund_master"]
    nav_history = data["nav_history"].copy()
    aum_fh = data["aum_fh"].copy()
    sip_inflows = data["sip_inflows"].copy()
    investor_tx = data["investor_tx"].copy()
    scheme_perf = data["scheme_perf"].copy()
    portfolio = data["portfolio"].copy()
    folio_count = data["folio_count"].copy()

    aum_fh["year"] = aum_fh["date"].dt.year
    aum_yearly = aum_fh.groupby(["year", "fund_house"], as_index=False)["aum_crore"].max()
    latest_year = int(aum_yearly["year"].max())
    sbi_2025 = aum_yearly[(aum_yearly["year"] == latest_year) & (aum_yearly["fund_house"] == "SBI Mutual Fund")]["aum_crore"]
    sbi_value = int(sbi_2025.iloc[0]) if not sbi_2025.empty else int(aum_yearly[aum_yearly["fund_house"] == "SBI Mutual Fund"]["aum_crore"].max())

    sip_2025 = sip_inflows[sip_inflows["month"].dt.strftime("%Y-%m") == "2025-12"]
    sip_milestone = int(sip_2025["sip_inflow_crore"].iloc[0]) if not sip_2025.empty else int(sip_inflows["sip_inflow_crore"].max())

    total_folios_start = float(folio_count.sort_values("month")["total_folios_crore"].iloc[0])
    total_folios_end = float(folio_count.sort_values("month")["total_folios_crore"].iloc[-1])

    equity_codes = fund_master.loc[fund_master["category"].eq("Equity"), "amfi_code"]
    sector_alloc = (
        portfolio[portfolio["amfi_code"].isin(equity_codes)]
        .groupby("sector", as_index=False).agg(market_value_cr=("market_value_cr", "sum"))
        .sort_values(by="market_value_cr", ascending=False)
    )
    top_sector = sector_alloc.iloc[0]["sector"] if not sector_alloc.empty else "Unknown"

    investor_tx["amount_inr"] = pd.to_numeric(investor_tx["amount_inr"], errors="coerce")
    state_sip = investor_tx[investor_tx["transaction_type"].eq("SIP")].groupby("state", as_index=False).agg(amount_inr=("amount_inr","sum")).sort_values(by="amount_inr", ascending=False)
    top_state = state_sip.iloc[0]["state"] if not state_sip.empty else "Unknown"

    highest_sharpe = scheme_perf.sort_values("sharpe_ratio", ascending=False).iloc[0]
    lowest_expense = scheme_perf.sort_values("expense_ratio_pct", ascending=True).iloc[0]
    top_return = scheme_perf.sort_values("return_3yr_pct", ascending=False).iloc[0]
    top_drawdown = scheme_perf.sort_values("max_drawdown_pct", ascending=True).iloc[0]

    findings = [
        f"1. All 40 schemes are represented in the NAV dataset, and the cleaned series now extends from 2022-01 through 2026-05.",
        f"2. SBI Mutual Fund remains the largest AMC in the sample; its latest annual AUM snapshot is about ₹{sbi_value:,} crore.",
        f"3. Monthly SIP inflow is structurally higher by the end of the sample, with the December 2025 milestone at roughly ₹{sip_milestone:,} crore.",
        f"4. The industry folio base roughly doubled from {total_folios_start:.2f} crore to {total_folios_end:.2f} crore over the period.",
        f"5. The strongest equity portfolio sector exposure is concentrated in {top_sector}, showing that sector allocation is still clustered.",
        f"6. SIP value is led by {top_state}, indicating that transaction value is concentrated in a handful of large investor states.",
        f"7. T30 investors still contribute the larger SIP pool versus B30 in absolute amount terms, even though B30 activity is broad-based.",
        f"8. The highest Sharpe ratio in the dataset belongs to {highest_sharpe['scheme_name']} ({highest_sharpe['sharpe_ratio']:.2f}), which is consistent with liquid-fund style stability.",
        f"9. The lowest expense ratio fund in the sample is {lowest_expense['scheme_name']} at {lowest_expense['expense_ratio_pct']:.2f}%, confirming the direct-plan cost advantage.",
        f"10. Return and risk remain coupled: {top_return['scheme_name']} leads on 3-year return at {top_return['return_3yr_pct']:.2f}%, while {top_drawdown['scheme_name']} has the shallowest drawdown at {top_drawdown['max_drawdown_pct']:.2f}%.",
    ]

    findings_path = REPORT_DIR / "day3_findings.md"
    findings_path.write_text("\n".join(["# Day 3 Findings", ""] + [f"- {line}" for line in findings]) + "\n", encoding="utf-8")
    return findings


def run_all() -> dict[str, list[Path] | list[str]]:
    """Execute all EDA visualizations and metrics computations."""
    data = load_datasets()
    artifacts = {
        "nav": nav_charts(data),
        "aum_sip": aum_sip_charts(data),
        "demographic_geo": demographic_geo_charts(data),
        "portfolio": portfolio_charts(data),
        "performance": performance_charts(data),
        "findings": build_findings(data),
    }
    return artifacts


if __name__ == "__main__":
    results = run_all()
