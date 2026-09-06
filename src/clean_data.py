"""
clean_data.py
-------------
Transforms raw Alpha Vantage JSON (one file per symbol) into a single,
clean, analysis-ready pandas DataFrame, and writes it out as CSV.

Usage:
    python src/clean_data.py
"""
import glob
import json
import os

import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_PATH = "data/processed/clean_prices.csv"


def load_latest_raw(symbol: str, raw_dir: str = RAW_DIR) -> dict:
    files = sorted(glob.glob(os.path.join(raw_dir, f"{symbol}_*.json")))
    if not files:
        raise FileNotFoundError(f"No raw data for {symbol}. Run fetch_data.py first.")
    with open(files[-1]) as f:
        return json.load(f)


def to_dataframe(raw: dict, symbol: str) -> pd.DataFrame:
    """Flatten Alpha Vantage's nested JSON into a tidy DataFrame."""
    series = raw["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(series, orient="index")

    # Alpha Vantage columns look like "1. open", "2. high" ... strip the prefix
    df.columns = [c.split(". ", 1)[1] for c in df.columns]
    df = df.astype(float)

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df["symbol"] = symbol
    df["daily_return_pct"] = df["close"].pct_change() * 100

    df = df.reset_index().rename(columns={"index": "date"})
    return df[["date", "symbol", "open", "high", "low", "close", "volume", "daily_return_pct"]]


def clean_all(symbols: list[str]) -> pd.DataFrame:
    frames = [to_dataframe(load_latest_raw(sym), sym) for sym in symbols]
    return pd.concat(frames, ignore_index=True)


def run(symbols: list[str] | None = None) -> pd.DataFrame:
    from fetch_data import DEFAULT_SYMBOLS  # reuse the same default list

    df = clean_all(symbols or DEFAULT_SYMBOLS)

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)

    print(f"Cleaned {len(df)} rows across {df['symbol'].nunique()} symbols")
    print(f"Saved -> {PROCESSED_PATH}")
    print(df.head())
    return df


if __name__ == "__main__":
    run()
