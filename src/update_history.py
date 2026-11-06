"""
update_history.py
-----------------
Merges the latest cleaned prices into a long-running history file that is
committed to the repo. Alpha Vantage's free "compact" endpoint only returns
the last ~100 trading days, so this stage is what lets the dataset keep
growing day after day when the pipeline runs on a schedule.

Upsert logic: (date, symbol) is the primary key. A newer fetch overwrites
an older row for the same key (prices can be revised after the close), and
new trading days are appended.

Usage:
    python src/update_history.py
"""
import os

import pandas as pd

PROCESSED_PATH = "data/processed/clean_prices.csv"
HISTORY_PATH = "data/history/price_history.csv"
KEY = ["date", "symbol"]


def merge_history(history: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    """Upsert `latest` into `history` on (date, symbol), newest values win."""
    combined = pd.concat([history, latest], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"])
    combined = combined.drop_duplicates(subset=KEY, keep="last")
    combined = combined.sort_values(KEY).reset_index(drop=True)

    # Recompute returns over the full history so the first row of each new
    # 100-day window doesn't end up with a missing (NaN) return.
    combined["daily_return_pct"] = (
        combined.groupby("symbol")["close"].pct_change() * 100
    )
    return combined


def run(processed_path: str = PROCESSED_PATH, history_path: str = HISTORY_PATH) -> pd.DataFrame:
    latest = pd.read_csv(processed_path, parse_dates=["date"])

    if os.path.exists(history_path):
        history = pd.read_csv(history_path, parse_dates=["date"])
    else:
        history = latest.iloc[0:0]

    before = len(history)
    merged = merge_history(history, latest)

    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    merged.to_csv(history_path, index=False, date_format="%Y-%m-%d", float_format="%.4f")

    print(f"History: {before} -> {len(merged)} rows ({len(merged) - before:+d} new)")
    print(f"Saved -> {history_path}")
    return merged


if __name__ == "__main__":
    run()
