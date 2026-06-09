"""
scripts/email_report.py
=======================
Generates a weekly Mutual Fund Performance HTML report and sends it via the Resend API.
Supports a --dry-run option to output a local HTML preview for design verification.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
import requests

# ─── Path Configuration ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

# Create target directory
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_env_variables() -> dict[str, str]:
    """Manually parse .env file in the root directory to avoid extra package requirements."""
    env_vars = {}
    env_path = BASE_DIR / ".env"
    
    # Also check if environment variables are set in OS
    for key in ["RESEND_API_KEY", "EMAIL_RECEIVER", "EMAIL_SENDER"]:
        if os.getenv(key):
            env_vars[key] = os.getenv(key)
            
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
                    
    # Default sender if none specified
    if "EMAIL_SENDER" not in env_vars:
        env_vars["EMAIL_SENDER"] = "onboarding@resend.dev"
        
    return env_vars


def fetch_report_data() -> dict:
    """Query SQLite database to build report indicators."""
    data = {}
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH.resolve()}")
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch overall Industry Stats (Latest Monthly SIP Inflow and Folio Growth)
    sip_df = pd_read_sql("SELECT month, sip_inflow_crore, active_sip_accounts_crore FROM fact_monthly_sip ORDER BY month DESC LIMIT 1", conn)
    folio_df = pd_read_sql("SELECT month, total_folios_crore FROM fact_folio_count ORDER BY month DESC LIMIT 1", conn)
    
    data["latest_month"] = sip_df[0]["month"] if sip_df else "N/A"
    data["sip_inflow_crore"] = sip_df[0]["sip_inflow_crore"] if sip_df else 0.0
    data["sip_accounts"] = sip_df[0]["active_sip_accounts_crore"] if sip_df else 0.0
    data["total_folios"] = folio_df[0]["total_folios_crore"] if folio_df else 0.0
    
    # 2. Fetch Top 5 Ranked Funds
    top_funds_query = """
        SELECT f.scheme_name, f.category, f.expense_ratio_pct,
               p.return_3yr_pct, p.sharpe_ratio, p.max_drawdown_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        ORDER BY (0.30 * p.return_3yr_pct + 0.25 * p.sharpe_ratio) DESC
        LIMIT 5
    """
    data["top_funds"] = pd_read_sql(top_funds_query, conn)
    
    # 3. Load Portfolio Optimization MSR weights from report output
    opt_csv_path = REPORTS_DIR / "day6" / "portfolio_optimization_results.csv"
    if opt_csv_path.exists():
        import csv
        with open(opt_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data["optimization_portfolios"] = list(reader)
    else:
        data["optimization_portfolios"] = []
        
    conn.close()
    return data


def pd_read_sql(query: str, conn: sqlite3.Connection) -> list[dict]:
    """Helper to convert SQL query result to list of dicts easily without pandas import overhead."""
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def build_html_template(data: dict) -> str:
    """Constructs a responsive, modern HTML email body using CSS utility classes."""
    
    # Build Top Funds Table rows
    table_rows = ""
    for idx, fund in enumerate(data["top_funds"]):
        scheme = fund["scheme_name"].split(" - ")[0]
        cat = fund["category"]
        ret_3y = f"{fund['return_3yr_pct']:.2f}%" if fund["return_3yr_pct"] else "-"
        sr = f"{fund['sharpe_ratio']:.2f}" if fund["sharpe_ratio"] else "-"
        dd = f"{fund['max_drawdown_pct']:.2f}%" if fund["max_drawdown_pct"] else "-"
        er = f"{fund['expense_ratio_pct']:.2f}%" if fund["expense_ratio_pct"] else "-"
        
        bg_color = "#f8fafc" if idx % 2 == 0 else "#ffffff"
        
        table_rows += f"""
        <tr style="background-color: {bg_color}; border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-size: 14px; font-weight: 600; color: #0f172a;">{scheme}</td>
            <td style="padding: 12px; font-size: 14px; color: #475569;">{cat}</td>
            <td style="padding: 12px; font-size: 14px; font-weight: bold; color: #10b981; text-align: right;">{ret_3y}</td>
            <td style="padding: 12px; font-size: 14px; font-weight: 600; color: #2563eb; text-align: right;">{sr}</td>
            <td style="padding: 12px; font-size: 14px; color: #dc2626; text-align: right;">{dd}</td>
            <td style="padding: 12px; font-size: 14px; color: #64748b; text-align: right;">{er}</td>
        </tr>
        """
        
    # Build Portfolio Optimization allocation rows
    opt_rows = ""
    if data["optimization_portfolios"]:
        # We look at the first row (MSR) and second row (MVP)
        for row in data["optimization_portfolios"]:
            ptype = "Maximum Sharpe Ratio (MSR)" if row["portfolio_type"] == "MSR" else "Minimum Volatility (MVP)"
            ret = f"{float(row['expected_annual_return_pct']):.2f}%"
            vol = f"{float(row['annual_volatility_pct']):.2f}%"
            sr = f"{float(row['sharpe_ratio']):.2f}"
            
            # Extract asset weights
            weights_str = ""
            for key, val in row.items():
                if key.startswith("weight_"):
                    fname = key.replace("weight_", "").replace("_", " ")
                    w_pct = float(val)
                    if w_pct > 1.0:
                        weights_str += f"<span style='display:inline-block; background-color:#e2e8f0; color:#0f172a; padding: 2px 6px; border-radius:4px; font-size:11px; margin-right:4px; margin-bottom:4px;'>{fname}: {w_pct:.1f}%</span>"
                        
            opt_rows += f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size: 15px; font-weight: bold; color: #0F766E; margin-bottom: 8px;">{ptype}</div>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
                    <tr>
                        <td style="font-size: 12px; color: #64748b; padding-right: 15px;">Expected Return</td>
                        <td style="font-size: 12px; color: #64748b; padding-right: 15px;">Portfolio Risk (Vol)</td>
                        <td style="font-size: 12px; color: #64748b;">Sharpe Ratio</td>
                    </tr>
                    <tr>
                        <td style="font-size: 16px; font-weight: bold; color: #10b981;">{ret}</td>
                        <td style="font-size: 16px; font-weight: bold; color: #2563eb;">{vol}</td>
                        <td style="font-size: 16px; font-weight: bold; color: #0f172a;">{sr}</td>
                    </tr>
                </table>
                <div style="border-top: 1px dashed #e2e8f0; padding-top: 8px; margin-top: 8px;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Asset Allocation:</div>
                    {weights_str}
                </div>
            </div>
            """
    else:
        opt_rows = "<p style='font-size:13px; color:#64748b;'>Optimal allocation metrics not available. Run the optimization pipeline first.</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Mutual Fund Performance Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f8fafc;
                color: #0f172a;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 680px;
                margin: 30px auto;
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}
            .header {{
                background-color: #0F766E;
                color: #ffffff;
                padding: 30px 40px;
                text-align: left;
            }}
            .content {{
                padding: 35px 40px;
            }}
            .footer {{
                background-color: #f1f5f9;
                border-top: 1px solid #e2e8f0;
                padding: 20px 40px;
                text-align: center;
                font-size: 12px;
                color: #64748b;
            }}
            .kpi-container {{
                display: table;
                width: 100%;
                margin-bottom: 30px;
                border-spacing: 12px 0;
            }}
            .kpi-card {{
                display: table-cell;
                width: 33.33%;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                vertical-align: top;
            }}
            .kpi-value {{
                font-size: 20px;
                font-weight: bold;
                color: #0f172a;
                margin-top: 4px;
            }}
            .kpi-title {{
                font-size: 11px;
                text-transform: uppercase;
                color: #64748b;
                letter-spacing: 0.5px;
            }}
            .kpi-subtext {{
                font-size: 10px;
                color: #94a3b8;
                margin-top: 4px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: bold;
                color: #0f172a;
                border-bottom: 2px solid #f1f5f9;
                padding-bottom: 8px;
                margin-top: 30px;
                margin-bottom: 15px;
            }}
            .btn-dash {{
                display: inline-block;
                background-color: #0F766E;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; color: #a5f3fc; margin-bottom: 5px;">Bluestock Fintech</div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 800; line-height: 1.2;">Weekly Mutual Fund Analytics Summary</h1>
                <div style="font-size: 13px; color: #e2f8f6; margin-top: 6px;">Automated performance & risk overview for top Indian schemes</div>
            </div>
            
            <div class="content">
                <p style="margin-top: 0; font-size: 14px; color: #475569; line-height: 1.6;">
                    Hello Investment Team, here is the weekly mutual fund performance summary. 
                    Macroeconomic data has been successfully fetched from AMFI India, transforming fund metrics inside the analytical database.
                </p>
                
                <div class="section-title">Industry High-Level Indicators</div>
                <div class="kpi-container">
                    <div class="kpi-card">
                        <div class="kpi-title">Monthly SIP Inflow</div>
                        <div class="kpi-value">₹{data["sip_inflow_crore"]:,.0f} Cr</div>
                        <div class="kpi-subtext">Record High ({data["latest_month"]})</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Active SIP Accounts</div>
                        <div class="kpi-value">{data["sip_accounts"]:.2f} Cr</div>
                        <div class="kpi-subtext">Registrations active</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Total MF Folios</div>
                        <div class="kpi-value">{data["total_folios"]:.2f} Cr</div>
                        <div class="kpi-subtext">Indian Retail accounts</div>
                    </div>
                </div>
                
                <div class="section-title">Top 5 Performing Mutual Fund Schemes</div>
                <div style="overflow-x: auto; width: 100%;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569; width: 40%;">Fund Name</th>
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569;">Category</th>
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569; text-align: right;">3Yr CAGR</th>
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569; text-align: right;">Sharpe</th>
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569; text-align: right;">Max DD</th>
                                <th style="padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #475569; text-align: right;">Expense</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
                
                <div class="section-title">Optimized Portfolios (Markowitz Frontier)</div>
                <p style="margin-top: 0; font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 15px;">
                    Allocations designed across the 5 representative mid, large, and flexicap mutual funds to achieve efficient returns:
                </p>
                {opt_rows}
                
                <div style="text-align: center; margin-top: 35px;">
                    <a href="https://bluestock.streamlit.app/" target="_blank" class="btn-dash">Open Interactive Dashboard</a>
                </div>
            </div>
            
            <div class="footer">
                <p style="margin: 0; font-weight: bold; color: #475569;">Bluestock Mutual Fund Analytics Platform</p>
                <p style="margin: 5px 0 0 0; color: #94a3b8;">This is an automated weekly summary report. To update scheduling settings, edit schedule_etl.bat on host environment.</p>
                <p style="margin: 15px 0 0 0; font-size: 11px; color: #94a3b8;">&copy; 2026 Bluestock Fintech Pvt. Ltd. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


def send_email(api_key: str, sender: str, receiver: str, html_body: str) -> bool:
    """Send the HTML content via the Resend API."""
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": sender,
        "to": receiver,
        "subject": "Weekly Mutual Fund Analytics Summary",
        "html": html_body
    }
    
    print(f"Connecting to Resend API to send report from {sender} to {receiver}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print(f"[SUCCESS] Email sent successfully! Message ID: {response.json().get('id')}")
            return True
        else:
            print(f"[ERROR] Resend API error: Status Code {response.status_code}")
            print(f"Details: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to send email via HTTP: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Weekly HTML Email Report Sender")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile metrics and write reports/weekly_report_preview.html without sending email."
    )
    args = parser.parse_args()
    
    print("Fetching metrics from database...")
    try:
        data = fetch_report_data()
    except Exception as e:
        print(f"[FATAL] Error fetching database report values: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("Compiling HTML email layout...")
    html_body = build_html_template(data)
    
    # Save local preview
    preview_file = REPORTS_DIR / "weekly_report_preview.html"
    with open(preview_file, "w", encoding="utf-8") as f:
        f.write(html_body)
    print(f"Local report preview successfully written to: {preview_file}")
    
    if args.dry_run:
        print("\n[INFO] Dry-run mode completed. Skipping email transmission.")
        return
        
    # Send email
    env = load_env_variables()
    api_key = env.get("RESEND_API_KEY", "")
    receiver = env.get("EMAIL_RECEIVER", "")
    sender = env.get("EMAIL_SENDER", "onboarding@resend.dev")
    
    if not api_key:
        print("\n[WARNING] RESEND_API_KEY not found in .env or OS environment.")
        print("          Please create a .env file or export the variable to send emails.")
        print("          Saved HTML preview is available at reports/weekly_report_preview.html.")
        return
        
    if not receiver:
        print("\n[WARNING] EMAIL_RECEIVER not found in .env or OS environment.")
        print("          Please specify who should receive the report (e.g. EMAIL_RECEIVER=your_email@example.com).")
        print("          Saved HTML preview is available at reports/weekly_report_preview.html.")
        return
        
    success = send_email(api_key, sender, receiver, html_body)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
