"""
Tests for update_history.py -- the upsert that lets the dataset grow
across scheduled runs without duplicating days.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from update_history import merge_history  # noqa: E402


def make_rows(rows):
    df = pd.DataFrame(rows, columns=["date", "symbol", "close"])
    df["date"] = pd.to_datetime(df["date"])
    df["daily_return_pct"] = float("nan")
    return df


def test_new_days_are_appended():
    history = make_rows([("2026-11-02", "AAPL", 100.0)])
    latest = make_rows([("2026-11-03", "AAPL", 110.0)])
    merged = merge_history(history, latest)
    assert len(merged) == 2


def test_duplicate_day_is_not_repeated_and_newest_wins():
    history = make_rows([("2026-11-02", "AAPL", 100.0)])
    latest = make_rows([("2026-11-02", "AAPL", 101.0)])
    merged = merge_history(history, latest)
    assert len(merged) == 1
    assert merged.iloc[0]["close"] == 101.0


def test_returns_recomputed_per_symbol_across_history():
    history = make_rows([("2026-11-02", "AAPL", 100.0), ("2026-11-02", "MSFT", 50.0)])
    latest = make_rows([("2026-11-03", "AAPL", 110.0), ("2026-11-03", "MSFT", 45.0)])
    merged = merge_history(history, latest).set_index(["symbol", "date"])
    assert round(merged.loc[("AAPL", pd.Timestamp("2026-11-03")), "daily_return_pct"], 4) == 10.0
    assert round(merged.loc[("MSFT", pd.Timestamp("2026-11-03")), "daily_return_pct"], 4) == -10.0


def test_output_sorted_by_date_then_symbol():
    history = make_rows([("2026-11-03", "MSFT", 1.0)])
    latest = make_rows([("2026-11-02", "AAPL", 1.0), ("2026-11-03", "AAPL", 1.0)])
    merged = merge_history(history, latest)
    assert list(zip(merged["date"].dt.strftime("%Y-%m-%d"), merged["symbol"])) == [
        ("2026-11-02", "AAPL"), ("2026-11-03", "AAPL"), ("2026-11-03", "MSFT"),
    ]
