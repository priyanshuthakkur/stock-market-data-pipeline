"""
update_readme.py
----------------
Final "reporting" stage: writes a fresh snapshot of the data (coverage,
latest closes, return stats) into README.md between two marker comments,
so the project page always shows the most recent run.

Usage:
    python src/update_readme.py
"""
import re
from datetime import datetime, timezone

import pandas as pd

from analyze import average_daily_return_by_symbol, query

README_PATH = "README.md"
START = "<!-- PIPELINE-STATS:START -->"
END = "<!-- PIPELINE-STATS:END -->"


def to_markdown_table(df: pd.DataFrame) -> str:
    """Small dependency-free markdown table (avoids needing `tabulate`)."""
    header = "| " + " | ".join(df.columns) + " |"
    divider = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, divider, *rows])


def build_stats_block() -> str:
    coverage = query(
        "SELECT COUNT(*) AS n_rows, COUNT(DISTINCT symbol) AS n_symbols, "
        "MIN(date) AS first_date, MAX(date) AS last_date FROM daily_prices"
    ).iloc[0]

    latest = query(
        """
        SELECT p.symbol, DATE(p.date) AS date, ROUND(p.close, 2) AS close_usd,
               ROUND(p.daily_return_pct, 2) AS day_change_pct
        FROM daily_prices p
        JOIN (SELECT symbol, MAX(date) AS max_date FROM daily_prices GROUP BY symbol) m
          ON p.symbol = m.symbol AND p.date = m.max_date
        ORDER BY p.symbol
        """
    )

    returns = average_daily_return_by_symbol()
    run_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return "\n".join([
        START,
        f"_Last automated run: **{run_time}** · "
        f"{coverage.n_rows:,} rows · {coverage.n_symbols} symbols · "
        f"{str(coverage.first_date)[:10]} to {str(coverage.last_date)[:10]}_",
        "",
        "**Latest close**",
        "",
        to_markdown_table(latest),
        "",
        "**Daily return statistics (full history)**",
        "",
        to_markdown_table(returns),
        END,
    ])


def update_readme(readme_path: str = README_PATH) -> None:
    with open(readme_path) as f:
        content = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        raise ValueError(f"Markers {START} / {END} not found in {readme_path}")

    block = build_stats_block()
    content = pattern.sub(lambda _: block, content)

    with open(readme_path, "w") as f:
        f.write(content)
    print(f"README stats refreshed -> {readme_path}")


if __name__ == "__main__":
    update_readme()
