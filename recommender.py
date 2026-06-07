import sqlite3
import argparse
import sys
from pathlib import Path

# Paths
BASE_DIR = Path("c:/repo/Mutual_Fund_Analysis")
DB_PATH = BASE_DIR / "database" / "bluestock_mf.db"

# Risk appetite mapping to database risk grades
RISK_MAPPING = {
    "low": ["Low"],
    "moderate": ["Moderate", "Moderately High"],
    "high": ["High", "Very High"]
}

def get_recommendations(risk_appetite):
    risk_appetite = risk_appetite.lower().strip()
    if risk_appetite not in RISK_MAPPING:
        print(f"Error: Invalid risk appetite '{risk_appetite}'. Must be 'Low', 'Moderate', or 'High'.")
        return []
    
    target_grades = RISK_MAPPING[risk_appetite]
    
    # Establish connection
    if not DB_PATH.exists():
        print(f"Error: SQLite database not found at {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Placeholders for IN clause
    placeholders = ",".join(["?"] * len(target_grades))
    
    query = f"""
        SELECT 
            amfi_code, 
            scheme_name, 
            category, 
            risk_grade, 
            sharpe_ratio,
            return_3yr_pct,
            aum_crore,
            morningstar_rating
        FROM fact_performance
        WHERE risk_grade IN ({placeholders})
        ORDER BY sharpe_ratio DESC
        LIMIT 3
    """
    
    try:
        cursor.execute(query, target_grades)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        results = []
    finally:
        conn.close()
        
    return results

def print_table(results, appetite):
    if not results:
        print("\nNo recommendations found for the selected appetite.")
        return
        
    title = f"TOP 3 FUND RECOMMENDATIONS FOR: {appetite.upper()} RISK APPETITE"
    print("\n" + "=" * 100)
    print(f" {title:^98} ")
    print("=" * 100)
    print(f"{'AMFI Code':<10} | {'Scheme Name':<45} | {'Category':<8} | {'Risk Grade':<15} | {'Sharpe':<6} | {'3Yr Ret':<8} | {'AUM (Cr)':<8}")
    print("-" * 100)
    
    for row in results:
        amfi, name, cat, risk_grade, sharpe, ret_3yr, aum, ms_rating = row
        # Truncate long scheme names for presentation
        disp_name = name[:43] + "..." if len(name) > 45 else name
        sharpe_str = f"{sharpe:.3f}" if sharpe is not None else "N/A"
        ret_str = f"{ret_3yr:.2f}%" if ret_3yr is not None else "N/A"
        aum_str = f"Rs.{aum:,}" if aum is not None else "N/A"
        
        print(f"{amfi:<10} | {disp_name:<45} | {cat:<8} | {risk_grade:<15} | {sharpe_str:<6} | {ret_str:<8} | {aum_str:<8}")
    print("=" * 100 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Mutual Fund Recommender CLI")
    parser.add_argument(
        "risk", 
        nargs="?", 
        choices=["Low", "Moderate", "High", "low", "moderate", "high"],
        help="Target investor risk appetite (Low, Moderate, High)"
    )
    args = parser.parse_args()
    
    appetite = args.risk
    
    if not appetite:
        print("\nWelcome to the Mutual Fund Recommender CLI!")
        print("Please choose your risk appetite:")
        print("  1. Low (Focus on capital preservation)")
        print("  2. Moderate (Balanced risk and return)")
        print("  3. High (Aggressive growth)")
        
        while True:
            choice = input("\nEnter choice (1-3 or Low/Moderate/High): ").strip().lower()
            if choice in ["1", "low"]:
                appetite = "Low"
                break
            elif choice in ["2", "moderate"]:
                appetite = "Moderate"
                break
            elif choice in ["3", "high"]:
                appetite = "High"
                break
            else:
                print("Invalid input. Please choose a valid risk appetite.")
                
    results = get_recommendations(appetite)
    print_table(results, appetite)

if __name__ == "__main__":
    main()
