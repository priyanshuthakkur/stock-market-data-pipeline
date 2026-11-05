"""
Unit tests for backtest.py. They use small made-up price series, so no
API key, network access or database is needed.

Usage:
    pytest
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from backtest import compare, crossover_positions, max_drawdown, run_backtest, summarise  # noqa: E402


def prices(values) -> pd.Series:
    dates = pd.date_range("2026-01-01", periods=len(values), freq="B")
    return pd.Series(values, index=dates, dtype=float)


def test_no_look_ahead_future_prices_do_not_change_past_positions():
    base = list(range(100, 160))
    close = prices(base)
    shocked = prices(base[:40] + [1.0] * 20)  # crash only after day 40
    original = crossover_positions(close, 3, 10)
    after_shock = crossover_positions(shocked, 3, 10)
    # Positions up to and including day 40 only depend on closes up to day 39.
    pd.testing.assert_series_equal(original.iloc[:41], after_shock.iloc[:41])


def test_signal_is_acted_on_the_next_day():
    close = prices(list(range(100, 130)))
    short_ma = close.rolling(3).mean()
    long_ma = close.rolling(10).mean()
    position = crossover_positions(close, 3, 10)
    day = 15
    assert position.iloc[day] == float(short_ma.iloc[day - 1] > long_ma.iloc[day - 1])


def test_short_window_must_be_shorter_than_long():
    with pytest.raises(ValueError):
        crossover_positions(prices([100] * 50), 30, 10)


def test_buy_and_hold_matches_price_change_over_the_same_window():
    close = prices([100 + i + (i % 5) for i in range(80)])
    result = run_backtest(close, 5, 20, cost_bps=0)
    first_day = result.index[0]
    start_price = close.iloc[close.index.get_loc(first_day) - 1]
    expected = close.iloc[-1] / start_price - 1
    assert summarise(result["buy_and_hold"])["total_return_pct"] == round(expected * 100, 2)


def test_trading_costs_reduce_strategy_returns():
    close = prices([100, 102, 98, 103, 97, 104, 96, 105] * 10)  # choppy, so it trades often
    free = run_backtest(close, 2, 5, cost_bps=0)
    costly = run_backtest(close, 2, 5, cost_bps=50)
    assert costly["strategy"].sum() < free["strategy"].sum()


def test_strategy_earns_nothing_while_in_cash():
    close = prices(list(range(200, 140, -1)))  # steady fall: short MA stays below long MA
    result = run_backtest(close, 3, 10, cost_bps=0)
    assert (result["position"] == 0).all()
    assert (result["strategy"] == 0).all()


def test_max_drawdown_known_example():
    # $1 -> 1.10 -> 0.88 -> 0.968: the worst fall is from 1.10 to 0.88 = -20%
    returns = pd.Series([0.10, -0.20, 0.10])
    assert max_drawdown(returns) == pytest.approx(-0.20)


def test_max_drawdown_counts_a_loss_on_the_first_day():
    # $1 -> 0.90 -> 0.95: a 10% fall from the starting $1
    assert max_drawdown(pd.Series([-0.10, 0.0556])) == pytest.approx(-0.10)


def test_compare_skips_symbols_with_too_little_data():
    rows = []
    for symbol, n in (("LONG", 120), ("SHORT", 25)):
        for i, d in enumerate(pd.date_range("2026-01-01", periods=n, freq="B")):
            rows.append({"date": d, "symbol": symbol, "close": 100 + i})
    summary, results = compare(pd.DataFrame(rows), 10, 30, cost_bps=5)
    assert set(summary["symbol"]) == {"LONG"}
    assert set(results) == {"LONG"}
