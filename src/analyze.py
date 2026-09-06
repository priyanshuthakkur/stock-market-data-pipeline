"""
analyze.py
----------
Runs SQL analysis against the loaded price data and exports a chart.
This is the "answer business questions with data" stage of the pipeline.

Usage:
    python src/analyze.py
"""
import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from load_db import DB_PATH


def query(sql: str, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def average_daily_return_by_symbol() -> pd.DataFrame:
    sql = """
        SELECT
            symbol,
            ROUND(AVG(daily_return_pct), 3) AS avg_daily_return_pct,
            ROUND(MAX(daily_return_pct), 3) AS best_day_pct,
            ROUND(MIN(daily_return_pct), 3) AS worst_day_pct
        FROM daily_prices
        GROUP BY symbol
        ORDER BY avg_daily_return_pct DESC;
    """
    return query(sql)


def plot_closing_prices(output_path: str = "outputs/closing_prices.png") -> str:
    df = query("SELECT date, symbol, close FROM daily_prices ORDER BY date")
    df["date"] = pd.to_datetime(df["date"])

    fig, ax = plt.subplots(figsize=(10, 5))
    for symbol, group in df.groupby("symbol"):
        ax.plot(group["date"], group["close"], label=symbol)

    ax.set_title("Closing Price Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price (USD)")
    ax.legend()
    fig.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    print(f"Chart saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    print("\nAverage daily return by symbol:\n")
    print(average_daily_return_by_symbol().to_string(index=False))
    plot_closing_prices()
