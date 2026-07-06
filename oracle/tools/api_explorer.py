"""
Oracle API Explorer

ORACLE-005.5

Purpose:
- Inspect real Kalshi API responses.
- Save raw JSON samples.
- Help Oracle build accurate parsers instead of guessing API shapes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from oracle.database.db import get_connection, init_db


KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
MARKET_SAMPLE_DIR = RAW_DIR / "market_samples"
ORDERBOOK_SAMPLE_DIR = RAW_DIR / "orderbook_samples"


def save_json_sample(folder: Path, filename: str, data: Dict[str, Any]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / filename

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)

    return path


def fetch_market_sample() -> Optional[Dict[str, Any]]:
    url = f"{KALSHI_BASE_URL}/markets"

    response = requests.get(
        url,
        params={
            "limit": 1,
        },
        timeout=20,
    )

    response.raise_for_status()
    data = response.json()

    markets = data.get("markets", [])

    if not markets:
        print("No markets returned.")
        return None

    return markets[0]


def get_latest_ticker_from_db() -> Optional[str]:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticker
        FROM markets
        WHERE ticker IS NOT NULL
        ORDER BY updated_at DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return row["ticker"]


def fetch_orderbook_sample(ticker: str) -> Dict[str, Any]:
    url = f"{KALSHI_BASE_URL}/markets/{ticker}/orderbook"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.json()


def print_keys(title: str, data: Dict[str, Any]) -> None:
    print("")
    print("=" * 60)
    print(title)
    print("=" * 60)

    for key, value in data.items():
        print(f"{key}: {type(value).__name__}")


def explore_api() -> None:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    print("Starting Oracle API Explorer...")

    market = fetch_market_sample()

    if market:
        market_path = save_json_sample(
            MARKET_SAMPLE_DIR,
            f"market_sample_{timestamp}.json",
            market,
        )

        print_keys("MARKET SAMPLE KEYS", market)
        print("")
        print(f"Saved market sample:")
        print(market_path)

    ticker = get_latest_ticker_from_db()

    if not ticker and market:
        ticker = market.get("ticker")

    if not ticker:
        print("No ticker available for orderbook sample.")
        return

    print("")
    print(f"Using ticker for orderbook sample: {ticker}")

    orderbook = fetch_orderbook_sample(ticker)

    orderbook_path = save_json_sample(
        ORDERBOOK_SAMPLE_DIR,
        f"orderbook_sample_{timestamp}_{ticker}.json",
        orderbook,
    )

    print_keys("ORDERBOOK SAMPLE TOP-LEVEL KEYS", orderbook)

    inner_orderbook = orderbook.get("orderbook")

    if isinstance(inner_orderbook, dict):
        print_keys("ORDERBOOK INNER KEYS", inner_orderbook)

    print("")
    print(f"Saved orderbook sample:")
    print(orderbook_path)

    print("")
    print("API exploration complete.")


if __name__ == "__main__":
    explore_api()