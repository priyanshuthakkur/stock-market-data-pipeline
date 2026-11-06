# Stock Market Data Pipeline

[![Daily pipeline run](https://github.com/priyanshuthakkur/stock-market-data-pipeline/actions/workflows/daily-pipeline.yml/badge.svg)](https://github.com/priyanshuthakkur/stock-market-data-pipeline/actions/workflows/daily-pipeline.yml)

A small end-to-end data pipeline: pull daily stock prices from a REST API,
clean and structure them with pandas, load them into a SQL database, then
answer questions about the data with SQL and a chart. It runs **automatically
every trading day** on GitHub Actions, so the dataset, chart and stats below
keep themselves up to date.

Built as a portfolio project to practise (and demonstrate) the core stack
behind most Data Analyst / Data Scientist / Data Engineer roles: **REST
APIs, Python, pandas, SQL, and Git** — end to end, not just in isolation.

## Pipeline

```
fetch_data.py ─▶ clean_data.py ─▶ update_history.py ─▶ load_db.py ─▶ analyze.py ─▶ update_readme.py
(REST API)       (pandas clean)   (upsert history)     (SQL load)    (SQL + chart)  (publish stats)
    │                 │                  │                  │              │               │
data/raw/*.json  data/processed/   data/history/      data/market_   outputs/        README.md
                 clean_prices.csv  price_history.csv  data.db        closing_prices.png
```

Each stage reads the previous stage's output and writes its own — the same
pattern used in real data infrastructure, just scaled down to run on a
laptop with no cloud account required.

## Sample output

![Closing price trend](outputs/closing_prices.png)

<!-- PIPELINE-STATS:START -->
_Stats appear here after the first automated run._
<!-- PIPELINE-STATS:END -->

## Automation (GitHub Actions)

[`.github/workflows/daily-pipeline.yml`](.github/workflows/daily-pipeline.yml)
turns the project into a scheduled batch job:

1. **Trigger**: cron at 22:47 UTC, Monday to Friday (after the US market
   close), plus a manual "Run workflow" button.
2. **Test**: runs the pytest suite first, so a broken change never touches the data.
3. **Run**: executes all six pipeline stages with the API key injected from
   an encrypted repository secret.
4. **Persist**: `update_history.py` upserts the newest prices into
   `data/history/price_history.csv` on `(date, symbol)`, so the dataset grows
   beyond the API's 100-day window without duplicate days.
5. **Publish**: commits the refreshed history, chart and README stats, and
   skips the commit entirely when there is no new market data.

To run it on your own fork, add a free Alpha Vantage key as the repository
secret `ALPHA_VANTAGE_API_KEY` (Settings → Secrets and variables → Actions).

## Getting started

```bash
# 1. Clone and enter the repo
git clone https://github.com/priyanshuthakkur/stock-market-data-pipeline.git
cd stock-market-data-pipeline

# 2. Set up a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your free Alpha Vantage API key
cp .env.example .env
# then edit .env and paste your key from https://www.alphavantage.co/support/#api-key

# 5. Run the full pipeline
python run_pipeline.py
```

Or run each stage individually:

```bash
python src/fetch_data.py
python src/clean_data.py
python src/update_history.py
python src/load_db.py
python src/analyze.py
python src/update_readme.py
```

Run the tests (no API key needed — they use mock data):

```bash
pip install pytest
pytest
```

## Project structure

```
stock-market-data-pipeline/
├── .github/workflows/
│   └── daily-pipeline.yml  # scheduled run, tests, auto-commit
├── src/
│   ├── fetch_data.py       # REST API ingestion
│   ├── clean_data.py       # pandas cleaning & transformation
│   ├── update_history.py   # incremental upsert into the history file
│   ├── load_db.py          # load into SQLite
│   ├── analyze.py          # SQL analysis + chart export
│   └── update_readme.py    # publishes latest stats to this README
├── tests/
│   ├── test_clean_data.py
│   └── test_update_history.py
├── data/
│   └── history/            # growing price history (committed); raw/processed/DB gitignored
├── outputs/               # exported charts
├── run_pipeline.py        # runs all four stages in sequence
├── requirements.txt
└── .env.example
```

## Skills demonstrated

| Area | Where |
|---|---|
| REST API integration | `fetch_data.py` — `requests` against Alpha Vantage's live API |
| Data cleaning & transformation | `clean_data.py` — pandas, type coercion, derived columns |
| SQL & relational data modelling | `load_db.py`, `analyze.py` — schema design, indexing, aggregate queries |
| Data pipeline design | `run_pipeline.py` — staged, fail-fast orchestration |
| Incremental loading | `update_history.py` — idempotent upsert on a composite key |
| Scheduling & CI/CD | `daily-pipeline.yml` — cron-triggered GitHub Actions, secrets, test gate, auto-commit |
| Testing | `tests/test_clean_data.py` — pytest, mock API payloads |
| Version control | commit history — staged, incremental commits rather than one dump |

## Extending this

The fetch → clean → load → analyze pattern here is deliberately generic —
swapping the API and the domain logic is enough to repurpose it. This is
the template for two companion projects: a healthcare version (image/tabular
data, tying into a deep learning dissertation) and a marketing analytics
version (engagement/campaign data with a dashboard layer).

## License

MIT — see [LICENSE](LICENSE).
