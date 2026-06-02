PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    plan TEXT NOT NULL,
    launch_date DATE,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code INTEGER NOT NULL,
    nav_date DATE NOT NULL,
    nav REAL NOT NULL,
    daily_return REAL,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    as_of_date DATE NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore INTEGER,
    num_schemes INTEGER,
    PRIMARY KEY (fund_house, as_of_date)
);

CREATE TABLE IF NOT EXISTS fact_monthly_sip (
    month DATE PRIMARY KEY,
    sip_inflow_crore INTEGER,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

CREATE TABLE IF NOT EXISTS fact_category_inflows (
    month DATE NOT NULL,
    category TEXT NOT NULL,
    net_inflow_crore REAL,
    PRIMARY KEY (month, category)
);

CREATE TABLE IF NOT EXISTS fact_folio_count (
    month DATE PRIMARY KEY,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    plan TEXT NOT NULL,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore INTEGER,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_holdings (
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date DATE NOT NULL,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_benchmark (
    benchmark_date DATE NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL,
    PRIMARY KEY (benchmark_date, index_name)
);
