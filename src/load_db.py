"""
load_db.py
----------
Loads the cleaned CSV into a local SQLite database. SQLite stands in here
for a cloud warehouse (Snowflake, BigQuery, etc.) -- same relational
modelling and SQL, no cloud account required to run this project.

Usage:
    python src/load_db.py
"""
import os
import sqlite3

import pandas as pd

DB_PATH = "data/market_data.db"
PROCESSED_PATH = "data/processed/clean_prices.csv"
TABLE_NAME = "daily_prices"


def load_to_sqlite(csv_path: str = PROCESSED_PATH, db_path: str = DB_PATH) -> None:
    df = pd.read_csv(csv_path, parse_dates=["date"])

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_symbol_date ON {TABLE_NAME}(symbol, date)"
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded {len(df)} rows into {db_path} -> table '{TABLE_NAME}'")


if __name__ == "__main__":
    load_to_sqlite()
