CREATE TABLE dim_fund (
    amfi_code INT NOT NULL PRIMARY KEY,
    fund_house NVARCHAR(200) NOT NULL,
    scheme_name NVARCHAR(300) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    sub_category NVARCHAR(100) NULL,
    variant_type NVARCHAR(50) NOT NULL,
    launch_date DATE NULL,
    benchmark NVARCHAR(200) NULL,
    expense_ratio_pct DECIMAL(10,4) NULL,
    exit_load_pct DECIMAL(10,4) NULL,
    min_sip_amount INT NULL,
    min_lumpsum_amount INT NULL,
    fund_manager NVARCHAR(200) NULL,
    risk_category NVARCHAR(100) NULL,
    sebi_category_code NVARCHAR(50) NULL
);

CREATE TABLE dim_date (
    date_value DATE NOT NULL PRIMARY KEY,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name NVARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name NVARCHAR(20) NOT NULL,
    is_weekend BIT NOT NULL
);

CREATE TABLE fact_nav (
    amfi_code INT NOT NULL,
    nav_date DATE NOT NULL,
    nav DECIMAL(18,4) NOT NULL,
    daily_return DECIMAL(18,6) NULL,
    CONSTRAINT pk_fact_nav PRIMARY KEY (amfi_code, nav_date),
    CONSTRAINT fk_fact_nav_fund FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    CONSTRAINT fk_fact_nav_date FOREIGN KEY (nav_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_aum (
    as_of_date DATE NOT NULL,
    fund_house NVARCHAR(200) NOT NULL,
    aum_lakh_crore DECIMAL(18,4) NULL,
    aum_crore INT NULL,
    num_schemes INT NULL,
    CONSTRAINT pk_fact_aum PRIMARY KEY (fund_house, as_of_date),
    CONSTRAINT fk_fact_aum_date FOREIGN KEY (as_of_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_monthly_sip (
    month DATE NOT NULL PRIMARY KEY,
    sip_inflow_crore INT NULL,
    active_sip_accounts_crore DECIMAL(18,4) NULL,
    new_sip_accounts_lakh DECIMAL(18,4) NULL,
    sip_aum_lakh_crore DECIMAL(18,4) NULL,
    yoy_growth_pct DECIMAL(18,4) NULL,
    CONSTRAINT fk_fact_monthly_sip_date FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_category_inflows (
    month DATE NOT NULL,
    category NVARCHAR(100) NOT NULL,
    net_inflow_crore DECIMAL(18,4) NULL,
    CONSTRAINT pk_fact_category_inflows PRIMARY KEY (month, category),
    CONSTRAINT fk_fact_category_inflows_date FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_folio_count (
    month DATE NOT NULL PRIMARY KEY,
    total_folios_crore DECIMAL(18,4) NULL,
    equity_folios_crore DECIMAL(18,4) NULL,
    debt_folios_crore DECIMAL(18,4) NULL,
    hybrid_folios_crore DECIMAL(18,4) NULL,
    others_folios_crore DECIMAL(18,4) NULL,
    CONSTRAINT fk_fact_folio_count_date FOREIGN KEY (month) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_performance (
    amfi_code INT NOT NULL PRIMARY KEY,
    scheme_name NVARCHAR(300) NOT NULL,
    fund_house NVARCHAR(200) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    variant_type NVARCHAR(50) NOT NULL,
    return_1yr_pct DECIMAL(10,4) NULL,
    return_3yr_pct DECIMAL(10,4) NULL,
    return_5yr_pct DECIMAL(10,4) NULL,
    benchmark_3yr_pct DECIMAL(10,4) NULL,
    alpha DECIMAL(10,4) NULL,
    beta DECIMAL(10,4) NULL,
    sharpe_ratio DECIMAL(10,4) NULL,
    sortino_ratio DECIMAL(10,4) NULL,
    std_dev_ann_pct DECIMAL(10,4) NULL,
    max_drawdown_pct DECIMAL(10,4) NULL,
    aum_crore INT NULL,
    expense_ratio_pct DECIMAL(10,4) NULL,
    morningstar_rating INT NULL,
    risk_grade NVARCHAR(100) NULL
);

CREATE TABLE fact_transactions (
    transaction_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    investor_id NVARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    amfi_code INT NOT NULL,
    transaction_type NVARCHAR(50) NOT NULL,
    amount_inr DECIMAL(18,2) NOT NULL,
    state NVARCHAR(100) NULL,
    city NVARCHAR(100) NULL,
    city_tier NVARCHAR(20) NULL,
    age_group NVARCHAR(20) NULL,
    gender NVARCHAR(20) NULL,
    annual_income_lakh DECIMAL(18,2) NULL,
    payment_mode NVARCHAR(50) NULL,
    kyc_status NVARCHAR(50) NULL,
    CONSTRAINT fk_fact_transactions_fund FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    CONSTRAINT fk_fact_transactions_date FOREIGN KEY (transaction_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_holdings (
    amfi_code INT NOT NULL,
    stock_symbol NVARCHAR(50) NOT NULL,
    stock_name NVARCHAR(200) NULL,
    sector NVARCHAR(100) NULL,
    weight_pct DECIMAL(10,4) NULL,
    market_value_cr DECIMAL(18,4) NULL,
    current_price_inr DECIMAL(18,4) NULL,
    portfolio_date DATE NOT NULL,
    CONSTRAINT pk_fact_holdings PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    CONSTRAINT fk_fact_holdings_fund FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    CONSTRAINT fk_fact_holdings_date FOREIGN KEY (portfolio_date) REFERENCES dim_date (date_value)
);

CREATE TABLE fact_benchmark (
    benchmark_date DATE NOT NULL,
    index_name NVARCHAR(100) NOT NULL,
    close_value DECIMAL(18,4) NULL,
    CONSTRAINT pk_fact_benchmark PRIMARY KEY (benchmark_date, index_name),
    CONSTRAINT fk_fact_benchmark_date FOREIGN KEY (benchmark_date) REFERENCES dim_date (date_value)
);
