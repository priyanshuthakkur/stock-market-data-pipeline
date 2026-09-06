"""
Unit tests for clean_data.py's transform logic.
Uses a small mock payload shaped like Alpha Vantage's real response,
so no network call or API key is needed to run these.

Usage:
    pytest
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clean_data import to_dataframe  # noqa: E402

MOCK_RAW = {
    "Meta Data": {"2. Symbol": "TEST"},
    "Time Series (Daily)": {
        "2026-09-03": {
            "1. open": "100.00",
            "2. high": "105.00",
            "3. low": "99.00",
            "4. close": "104.00",
            "5. volume": "1000000",
        },
        "2026-09-04": {
            "1. open": "104.00",
            "2. high": "108.00",
            "3. low": "103.00",
            "4. close": "107.00",
            "5. volume": "1200000",
        },
    },
}


def test_to_dataframe_shape():
    df = to_dataframe(MOCK_RAW, "TEST")
    assert len(df) == 2
    assert list(df.columns) == [
        "date", "symbol", "open", "high", "low", "close", "volume", "daily_return_pct",
    ]


def test_to_dataframe_is_sorted_by_date():
    df = to_dataframe(MOCK_RAW, "TEST")
    assert df["date"].is_monotonic_increasing


def test_daily_return_calculation():
    df = to_dataframe(MOCK_RAW, "TEST")
    # second day: (107 - 104) / 104 * 100
    expected_return = (107.0 - 104.0) / 104.0 * 100
    assert round(df.iloc[1]["daily_return_pct"], 4) == round(expected_return, 4)


def test_symbol_column_populated():
    df = to_dataframe(MOCK_RAW, "TEST")
    assert (df["symbol"] == "TEST").all()
