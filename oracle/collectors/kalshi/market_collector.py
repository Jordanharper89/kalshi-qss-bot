"""
Oracle Kalshi Market Collector

ORACLE-003 / ORACLE-005.6

Purpose:
- Pull active Kalshi markets from the public Kalshi API.
- Store/update raw market facts in Oracle's SQLite database.
- Parse real Kalshi dollar fields into cents.
- No trading.
- No fair value logic.
- No signal generation.
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from oracle.database.db import get_connection, init_db


KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


def safe_get(data: Dict[str, Any], *keys: str, default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def dollars_to_cents(value) -> Optional[float]:
    if value is None or value == "":
        return None

    try:
        return round(float(value) * 100, 4)
    except (TypeError, ValueError):
        return None


def fp_to_number(value) -> int:
    if value is None or value == "":
        return 0

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def fetch_markets(limit: int = 200, max_pages: int = 5) -> List[Dict[str, Any]]:
    all_markets = []
    cursor: Optional[str] = None

    for page in range(max_pages):
        params = {
            "limit": limit,
            "status": "open",
        }

        if cursor:
            params["cursor"] = cursor

        url = f"{KALSHI_BASE_URL}/markets"

        print(f"Fetching Kalshi markets page {page + 1}...")

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        data = response.json()

        markets = data.get("markets", [])
        all_markets.extend(markets)

        cursor = data.get("cursor")

        if not cursor:
            break

        time.sleep(0.25)

    return all_markets


def save_markets(markets: List[Dict[str, Any]]) -> int:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    saved_count = 0

    for market in markets:
        ticker = safe_get(market, "ticker")
        if not ticker:
            continue

        yes_bid = dollars_to_cents(market.get("yes_bid_dollars"))
        yes_ask = dollars_to_cents(market.get("yes_ask_dollars"))
        no_bid = dollars_to_cents(market.get("no_bid_dollars"))
        no_ask = dollars_to_cents(market.get("no_ask_dollars"))

        last_price = dollars_to_cents(market.get("last_price_dollars"))

        yes_price = yes_ask if yes_ask is not None else last_price
        no_price = no_ask

        market_title = safe_get(market, "title", default="")
        category = safe_get(market, "market_type", "event_ticker", default="unknown")

        expiration_time = safe_get(
            market,
            "close_time",
            "expiration_time",
            "expected_expiration_time",
            default=None,
        )

        status = safe_get(market, "status", default="unknown")

        volume = fp_to_number(safe_get(market, "volume_fp", "volume_24h_fp", default=0))
        open_interest = fp_to_number(safe_get(market, "open_interest_fp", default=0))

        raw_json = json.dumps(market, sort_keys=True)

        cursor.execute(
            """
            INSERT INTO markets (
                ticker,
                market_title,
                category,
                expiration_time,
                status,
                yes_price,
                no_price,
                volume,
                open_interest,
                raw_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ticker) DO UPDATE SET
                market_title = excluded.market_title,
                category = excluded.category,
                expiration_time = excluded.expiration_time,
                status = excluded.status,
                yes_price = excluded.yes_price,
                no_price = excluded.no_price,
                volume = excluded.volume,
                open_interest = excluded.open_interest,
                raw_json = excluded.raw_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                ticker,
                market_title,
                category,
                expiration_time,
                status,
                yes_price,
                no_price,
                volume,
                open_interest,
                raw_json,
            ),
        )

        saved_count += 1

    conn.commit()
    conn.close()

    return saved_count


def collect_kalshi_markets() -> int:
    markets = fetch_markets()
    saved_count = save_markets(markets)

    print("Kalshi market collection complete.")
    print(f"Markets fetched: {len(markets)}")
    print(f"Markets saved: {saved_count}")

    return saved_count


if __name__ == "__main__":
    collect_kalshi_markets()