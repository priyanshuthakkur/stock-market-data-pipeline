"""
run_pipeline.py
----------------
Runs the full pipeline end-to-end:
fetch -> clean -> update history -> load -> analyze -> refresh README.

Usage:
    python run_pipeline.py
"""
import subprocess
import sys

STAGES = [
    "src/fetch_data.py",
    "src/clean_data.py",
    "src/update_history.py",
    "src/load_db.py",
    "src/analyze.py",
    "src/update_readme.py",
]


def run_pipeline() -> None:
    for stage in STAGES:
        print(f"\n{'=' * 50}\nRunning {stage}\n{'=' * 50}")
        result = subprocess.run([sys.executable, stage])
        if result.returncode != 0:
            print(f"\nPipeline stopped: {stage} failed.")
            sys.exit(1)
    print("\nPipeline complete. See outputs/closing_prices.png, data/history/ and README.md")


if __name__ == "__main__":
    run_pipeline()
