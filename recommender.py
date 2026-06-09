"""
recommender.py
==============
Launcher stub for Mutual Fund Recommender CLI.
Delegates execution to scripts/recommender.py.
"""

import os
import sys
import subprocess

def main():
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "recommender.py")
    cmd = [sys.executable, script_path] + sys.argv[1:]
    
    try:
        # Run scripts/recommender.py as a subprocess and exit with its return code
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running recommender: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
