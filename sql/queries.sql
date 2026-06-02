-- Q1: Top 5 funds by AUM
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    aum_crore,
    expense_ratio_pct,
    risk_grade
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- Q2: Average NAV per month
SELECT
    strftime('%Y-%m', nav_date) AS month,
    ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY strftime('%Y-%m', nav_date)
ORDER BY month;

-- Q3: SIP inflow YoY growth
SELECT
    strftime('%Y', month) AS year,
    ROUND(AVG(yoy_growth_pct), 2) AS avg_yoy_growth_pct,
    ROUND(SUM(sip_inflow_crore), 2) AS total_sip_inflow_crore
FROM fact_monthly_sip
WHERE yoy_growth_pct IS NOT NULL
GROUP BY strftime('%Y', month)
ORDER BY year;

-- Q4: Transactions by state
SELECT
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC
LIMIT 10;

-- Q5: Funds with expense_ratio < 1%
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC, scheme_name ASC;

-- Q6: Average 3-year return by category
SELECT
    category,
    ROUND(AVG(return_3yr_pct), 2) AS avg_return_3yr_pct,
    ROUND(AVG(benchmark_3yr_pct), 2) AS avg_benchmark_3yr_pct,
    ROUND(AVG(alpha), 2) AS avg_alpha
FROM fact_performance
GROUP BY category
ORDER BY avg_return_3yr_pct DESC;

-- Q7: Top 10 funds by Sharpe ratio
SELECT
    scheme_name,
    fund_house,
    category,
    plan,
    sharpe_ratio,
    sortino_ratio,
    expense_ratio_pct
FROM fact_performance
ORDER BY sharpe_ratio DESC, sortino_ratio DESC
LIMIT 10;

-- Q8: Top sectors in portfolio holdings by total market value
SELECT
    sector,
    COUNT(*) AS holding_rows,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct
FROM fact_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 10;

-- Q9: Latest NAV coverage by fund house
WITH latest_nav AS (
    SELECT amfi_code, MAX(nav_date) AS latest_nav_date
    FROM fact_nav
    GROUP BY amfi_code
)
SELECT
    f.fund_house,
    COUNT(*) AS schemes_covered,
    MIN(l.latest_nav_date) AS earliest_latest_date,
    MAX(l.latest_nav_date) AS latest_latest_date
FROM latest_nav l
JOIN dim_fund f ON f.amfi_code = l.amfi_code
GROUP BY f.fund_house
ORDER BY schemes_covered DESC, f.fund_house;

-- Q10: Benchmark averages by index
SELECT
    index_name,
    ROUND(AVG(close_value), 2) AS avg_close_value,
    ROUND(MIN(close_value), 2) AS min_close_value,
    ROUND(MAX(close_value), 2) AS max_close_value
FROM fact_benchmark
GROUP BY index_name
ORDER BY index_name;
