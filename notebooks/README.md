# 📓 Notebooks Directory

This directory contains Jupyter notebooks documenting the exploratory and analytical phases of the sprint.

## 📄 File Details

1. **`day1_eda_fund_master.ipynb`**: Day 1 initial setup, AMFI code validation, and fund master analysis.
2. **`EDA_Analysis.ipynb`**: Day 3 deep exploratory data analysis. Visualizes NAV trend lines, AUM and SIP growth, investor demographics, and equity portfolio sector allocations.
3. **`Performance_Analytics.ipynb`**: Day 4 fund performance computations. Documents mathematical formulas for daily returns, annualized returns, CAGR, Sharpe, Sortino, Alpha, Beta, Max Drawdown, and Tracking Error.
4. **`Advanced_Analytics.ipynb`**: Day 6 advanced analytics. Implements Value at Risk (VaR), Conditional VaR (CVaR), rolling Sharpe ratio volatility, cohort clustering, and Herfindahl-Hirschman Index (HHI) calculations.

## ⚙️ Running Notebooks
To open and run the notebooks:
```bash
jupyter notebook
```
Select the target notebook and run all cells. All notebooks read data from `data/processed/` or the SQLite database and output their logs/figures in the `reports/` folder.
