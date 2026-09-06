"""
fetch_data.py
--------------
Pulls daily stock price time series from Alpha Vantage's free REST API
and saves the raw JSON response to disk.

This is the "ingestion" stage of the pipeline: fetch_data.py -> clean_data.py
-> load_db.py -> analyze.py

Usage:
    python src/fetch_data.py
"""
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()  # reads ALPHA_VANTAGE_API_KEY from a local .env file

BASE_URL = "https://www.alphavantage.co/query"
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL"]


def fetch_daily_prices(symbol: str, api_key: str) -> dict:
    """
    Call Alpha Vantage's TIME_SERIES_DAILY endpoint for a single symbol.

    Raises:
        ValueError: if the API returns an error or rate-limit message
        requests.HTTPError: if the HTTP request itself fails
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",  # last ~100 trading days
        "apikey": api_key,
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        # Alpha Vantage returns 200 OK even for errors/rate limits,
        # so we have to check the payload shape ourselves.
        raise ValueError(f"Unexpected response for {symbol}: {data}")

    return data


def save_raw(symbol: str, data: dict, raw_dir: str = "data/raw") -> str:
    """Persist the raw API response as timestamped JSON."""
    os.makedirs(raw_dir, exist_ok=True)
    filename = os.path.join(raw_dir, f"{symbol}_{datetime.now():%Y%m%d}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename


def run(symbols: list[str] | None = None) -> None:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ALPHA_VANTAGE_API_KEY not set. Get a free key at "
            "https://www.alphavantage.co/support/#api-key and add it to a .env file:\n"
            "  ALPHA_VANTAGE_API_KEY=your_key_here"
        )

    for symbol in symbols or DEFAULT_SYMBOLS:
        print(f"Fetching {symbol}...")
        raw = fetch_daily_prices(symbol, api_key)
        path = save_raw(symbol, raw)
        print(f"  saved -> {path}")


if __name__ == "__main__":
    run()
