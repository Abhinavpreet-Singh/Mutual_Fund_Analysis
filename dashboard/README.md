# Power BI / Tableau Connection & Modeling Guide

This guide describes how to connect Power BI and Tableau to the relational SQLite database `database/bluestock_mf.db` and rebuild the boxy, modern white mutual fund analytics dashboard.

---

## 🛠️ Step 1: Connect Power BI to SQLite Database

Power BI does not support SQLite databases natively out of the box. You must connect via an **ODBC Driver**.

### 1. Install SQLite ODBC Driver
1. Download the driver from Christian Werner's page: [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/).
2. Select either `sqliteodbc.exe` (32-bit) or `sqliteodbc_w64.exe` (64-bit) depending on your Windows OS and Excel/Power BI installation. (Usually, the **64-bit** version `sqliteodbc_w64.exe` is required).
3. Run the installer.

### 2. Configure Windows ODBC Data Source (DSN)
1. In the Windows search bar, type **ODBC Data Sources (64-bit)** and open the application.
2. Under the **User DSN** or **System DSN** tab, click **Add...**.
3. Select the **SQLite 3 ODBC Driver** and click **Finish**.
4. Configure the Data Source:
   - **Data Source Name**: Enter `Bluestock_MF`
   - **Database Name**: Click **Browse...** and navigate to your local clone, then select `database/bluestock_mf.db` (e.g. `C:\repo\Mutual_Fund_Analysis\database\bluestock_mf.db`).
5. Click **OK** to save the DSN configuration.

### 3. Load Data into Power BI
1. Open **Power BI Desktop**.
2. Click **Get Data** > **More...** > **ODBC** and click **Connect**.
3. Under the **Data source name (DSN)** dropdown, select `Bluestock_MF` and click **OK**.
4. In the Navigator window, select the following 8 core tables:
   - `dim_fund`
   - `dim_date`
   - `fact_nav`
   - `fact_aum`
   - `fact_monthly_sip`
   - `fact_category_inflows`
   - `fact_folio_count`
   - `fact_performance`
   - `fact_transactions`
   - `fact_holdings`
   - `fact_benchmark`
5. Click **Load** to import them into the data model.

---

## 🔗 Step 2: Establish Model Relationships (Star Schema)

Once the tables load, click on the **Model View** tab on the left sidebar of Power BI and establish the following relationships to form a clean Star Schema:

1. **`dim_fund` ➔ `fact_nav`**
   - Keys: `amfi_code` to `amfi_code`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single** (dim_fund filters fact_nav)

2. **`dim_fund` ➔ `fact_transactions`**
   - Keys: `amfi_code` to `amfi_code`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

3. **`dim_fund` ➔ `fact_holdings`**
   - Keys: `amfi_code` to `amfi_code`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

4. **`dim_fund` ➔ `fact_performance`**
   - Keys: `amfi_code` to `amfi_code`
   - Cardinality: **1 to 1 (1:1)** (amfi_code is PK in both)
   - Cross filter direction: **Both**

5. **`dim_date` ➔ `fact_nav`**
   - Keys: `date_value` to `nav_date`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

6. **`dim_date` ➔ `fact_transactions`**
   - Keys: `date_value` to `transaction_date`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

7. **`dim_date` ➔ `fact_aum`**
   - Keys: `date_value` to `as_of_date`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

8. **`dim_date` ➔ `fact_benchmark`**
   - Keys: `date_value` to `benchmark_date`
   - Cardinality: **1 to Many (1:*)**
   - Cross filter direction: **Single**

---

## 🎨 Step 3: Configure Theme & Visual Styling

To match the requested **Clean Modern White** layout, apply these formatting rules inside Power BI:

- **Theme Palette**:
  - Primary (Teal): `#0F766E`
  - Secondary (Blue): `#2563EB`
  - Accent (Purple): `#7C3AED`
  - Danger (Red): `#DC2626`
  - Warning (Orange): `#F59E0B`
  - Light Background: `#F8FAFC`
- **Page Background**: Set canvas background color to `#F8FAFC` with 0% transparency.
- **Card Layout**:
  - Use boxy cards with sharp borders.
  - Turn on **Visual Border**: Set color to `#E2E8F0` and set Rounded Corners to `8px`.
  - Turn on **Shadow**: Color `#0F172A` at 5% opacity, offset = 1px.
  - Background color = `#FFFFFF`.
- **Typography**: Set all title and text fonts to **Segoe UI** or **Segoe UI Semibold** (for header titles) as it is clean, modern, and natively supported by Windows and Power BI.

---

## 📊 Step 4: Rebuild the 4 Dashboard Pages

### PAGE 1 — Industry Overview
- **KPI Card 1**: Total AUM (sum `fact_aum[aum_crore]`, display unit = Lakh Crore)
- **KPI Card 2**: SIP Inflows (sum `fact_monthly_sip[sip_inflow_crore]`, display unit = Crore)
- **KPI Card 3**: Folio Base (max `fact_folio_count[total_folios_crore]`, display unit = None, format = `#,##.00 Cr`)
- **KPI Card 4**: Schemes (count `dim_fund[amfi_code]`)
- **Line Chart**: Axis = `dim_date[date_value]`, Values = `fact_aum[aum_crore]`. Set line color to `#0F766E` (Teal), width = 3px.
- **Bar Chart**: Axis = `fact_performance[fund_house]`, Values = `fact_performance[aum_crore]`. Set color to `#2563EB` (Blue). Sort descending, top 10.

### PAGE 2 — Fund Performance
- **Slicers**:
  - Slicer 1: `dim_fund[fund_house]` (Dropdown)
  - Slicer 2: `dim_fund[category]` (Dropdown)
  - Slicer 3: `dim_fund[variant_type]` (Dropdown)
- **Scatter Plot (Risk-Return)**:
  - X-Axis: `fact_performance[return_3yr_pct]` (Return)
  - Y-Axis: `fact_performance[std_dev_ann_pct]` (Risk)
  - Details: `fact_performance[scheme_name]`
  - Legend: `fact_performance[category]`
  - Size: `fact_performance[aum_crore]`
- **Table (Scorecard)**: Columns: `Rank`, `Scheme Name`, `Category`, `3yr Return (%)`, `Sharpe Ratio`, `Composite Score`. Set header row background to `#F8FAFC`.
- **Drill-through / Tooltip**: Configure a line chart visual (Axis = `fact_nav[nav_date]`, Value = `fact_nav[nav]`) as a tooltip or target drill-through page linked from the scorecard table.

### PAGE 3 — Investor Analytics
- **Slicers**:
  - Slicer 1: `fact_transactions[state]`
  - Slicer 2: `fact_transactions[city_tier]`
- **Horizontal Bar Chart**: Axis = `fact_transactions[state]`, Values = `fact_transactions[amount_inr]`. Filter top 15 states.
- **Donut Chart**: Legend = `fact_transactions[transaction_type]`, Values = `fact_transactions[amount_inr]`.
- **Column Chart**: Axis = `fact_transactions[age_group]`, Values = Average of `fact_transactions[amount_inr]`. Filter transactions where `transaction_type = 'SIP'`.
- **Line Chart**: Axis = `dim_date[month]`, Values = count of `fact_transactions[transaction_id]`.

### PAGE 4 — SIP & Market Trends
- **Dual Axis Line & Clustered Column Chart**:
  - Shared Axis: `fact_monthly_sip[month]`
  - Column Values: `fact_monthly_sip[sip_inflow_crore]`
  - Line Values: `fact_benchmark[close_value]` (filtered for index_name = 'NIFTY50')
- **Heatmap (Matrix Visual)**:
  - Rows: `fact_category_inflows[category]`
  - Columns: `fact_category_inflows[month]`
  - Values: `fact_category_inflows[net_inflow_crore]`
  - Conditional Formatting: Apply background color scales (Green for positive, Red for negative).
- **Column Chart**: Axis = `fact_category_inflows[category]`, Values = Sum `fact_category_inflows[net_inflow_crore]`. Filter for Top 5 categories.