"""
backtest.py
-----------
Backtests a simple moving-average crossover strategy on the prices loaded
by load_db.py, and compares it with simply buying and holding each stock.

The strategy: be invested when the short moving average of the closing
price is above the long moving average, and hold cash otherwise.

Two rules keep the test honest:
- No look-ahead: a signal worked out from day t's close is only acted on
  from day t+1, so the strategy never trades on prices it couldn't have seen.
- Same window for both: the strategy and buy-and-hold are measured over
  exactly the same days (from the first day the long average exists).

Usage:
    python src/backtest.py
    python src/backtest.py --short 10 --long 30 --cost-bps 5
"""
import argparse
import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from load_db import DB_PATH

TRADING_DAYS_PER_YEAR = 252
OUTPUT_PATH = "outputs/backtest_equity.png"


def load_prices(db_path: str = DB_PATH) -> pd.DataFrame:
    """Read daily closing prices for every symbol from SQLite, oldest first."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT date, symbol, close FROM daily_prices ORDER BY symbol, date", conn
        )
    finally:
        conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


def crossover_positions(close: pd.Series, short: int, long: int) -> pd.Series:
    """
    1 = invested, 0 = in cash, for each day.

    The position held on day t is decided from closes up to day t-1, hence
    the shift(1). Days before the long average exists are NaN.
    """
    if short >= long:
        raise ValueError("The short window must be shorter than the long window.")
    short_ma = close.rolling(short).mean()
    long_ma = close.rolling(long).mean()
    signal = (short_ma > long_ma).astype(float).where(long_ma.notna())
    return signal.shift(1)


def run_backtest(close: pd.Series, short: int, long: int, cost_bps: float = 5.0) -> pd.DataFrame:
    """
    Daily returns for the strategy and for buy-and-hold over the same days.

    cost_bps is charged on each change of position (buy or sell), in basis
    points of the amount traded: 5 bps = 0.05% per trade.
    """
    daily_return = close.pct_change()
    position = crossover_positions(close, short, long)

    trades = position.diff().abs().fillna(0)
    strategy = position * daily_return - trades * cost_bps / 10_000

    result = pd.DataFrame(
        {"position": position, "strategy": strategy, "buy_and_hold": daily_return}
    )
    # Keep only days where the strategy had a defined position, so both
    # series cover exactly the same period.
    return result[result["position"].notna()]


def max_drawdown(returns: pd.Series) -> float:
    """Largest fall from a previous peak in the growth of $1, as a negative fraction."""
    equity = (1 + returns).cumprod()
    peak = equity.cummax().clip(lower=1.0)  # the starting $1 counts as a peak
    return float((equity / peak - 1).min())


def summarise(returns: pd.Series) -> dict:
    """Headline performance numbers for one daily return series."""
    days = len(returns)
    total = float((1 + returns).prod() - 1)
    volatility = float(returns.std() * TRADING_DAYS_PER_YEAR ** 0.5)
    mean = float(returns.mean() * TRADING_DAYS_PER_YEAR)
    return {
        "days": days,
        "total_return_pct": round(total * 100, 2),
        "annual_volatility_pct": round(volatility * 100, 2),
        # Risk-free rate taken as 0 for simplicity; None when there is no variation.
        "sharpe": round(mean / volatility, 2) if volatility > 0 else None,
        "max_drawdown_pct": round(max_drawdown(returns) * 100, 2),
    }


def compare(prices: pd.DataFrame, short: int, long: int, cost_bps: float) -> tuple[pd.DataFrame, dict]:
    """Backtest every symbol; return a summary table and the daily results per symbol."""
    rows, results = [], {}
    for symbol, group in prices.groupby("symbol"):
        close = group.set_index("date")["close"]
        if len(close) < long + 20:
            print(f"  ! {symbol}: only {len(close)} days of data, too few for a {long}-day average. Skipping.")
            continue
        result = run_backtest(close, short, long, cost_bps)
        results[symbol] = result
        trades = int(result["position"].diff().abs().fillna(0).sum())
        for name in ("strategy", "buy_and_hold"):
            rows.append({
                "symbol": symbol,
                "approach": f"SMA {short}/{long}" if name == "strategy" else "Buy and hold",
                **summarise(result[name]),
                "trades": trades if name == "strategy" else 1,
                "time_in_market_pct": round(result["position"].mean() * 100, 1) if name == "strategy" else 100.0,
            })
    return pd.DataFrame(rows), results


def equity_curve(returns: pd.Series) -> pd.Series:
    """Growth of $1, starting from exactly $1 the day before the first return."""
    start = pd.Series([1.0], index=[returns.index[0] - pd.Timedelta(days=1)])
    return pd.concat([start, (1 + returns).cumprod()])


def plot_equity(results: dict, short: int, long: int, output_path: str = OUTPUT_PATH) -> str:
    """One panel per symbol: growth of $1 for the strategy vs buy-and-hold."""
    fig, axes = plt.subplots(len(results), 1, figsize=(10, 3.2 * len(results)), squeeze=False)
    for ax, (symbol, result) in zip(axes[:, 0], results.items()):
        ax.plot(equity_curve(result["buy_and_hold"]), label="Buy and hold", color="#7f7f7f")
        ax.plot(equity_curve(result["strategy"]), label=f"SMA {short}/{long}", color="#1f3864")
        ax.axhline(1.0, color="#cccccc", linewidth=0.8, zorder=0)
        ax.set_title(symbol)
        ax.set_ylabel("Growth of $1")
        ax.legend(loc="upper left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Chart saved -> {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest a moving-average crossover strategy.")
    parser.add_argument("--short", type=int, default=10, help="short moving average, in days")
    parser.add_argument("--long", type=int, default=30, help="long moving average, in days")
    parser.add_argument("--cost-bps", type=float, default=5.0, help="cost per trade, in basis points")
    args = parser.parse_args()

    summary, results = compare(load_prices(), args.short, args.long, args.cost_bps)
    if summary.empty:
        raise SystemExit("Not enough data to backtest. Fetch a longer history first (see README).")

    print(f"\nSMA {args.short}/{args.long} crossover vs buy and hold "
          f"(cost {args.cost_bps:g} bps per trade):\n")
    print(summary.to_string(index=False))
    plot_equity(results, args.short, args.long)


if __name__ == "__main__":
    main()
