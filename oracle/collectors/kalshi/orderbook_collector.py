"""
Oracle Kalshi Order Book Snapshot Collector

ORACLE-004 / ORACLE-006.1

Purpose:
- Select higher-quality Kalshi markets first.
- Pull Kalshi order books.
- Store bid/ask/spread/depth snapshots forever.
- Avoid low-quality multi-leg noise when possible.
- No trading.
- No fair value logic.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from oracle.database.db import get_connection, init_db


KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


def extract_normalization(raw_json: str) -> Dict[str, Any]:
    if not raw_json:
        return {}

    try:
        raw = json.loads(raw_json)
        return raw.get("oracle_normalization", {}) or {}
    except Exception:
        return {}


def fetch_active_tickers(limit: int = 25) -> List[str]:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM markets")
    total_markets = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM markets
        WHERE yes_price > 0
        AND yes_price < 100
        """
    )
    useful_markets = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT ticker, market_title, yes_price, volume, open_interest, raw_json
        FROM markets
        WHERE yes_price > 0
        AND yes_price < 100
        ORDER BY open_interest DESC, volume DESC, updated_at DESC
        LIMIT 300
        """
    )

    rows = cursor.fetchall()
    conn.close()

    scored = []

    for row in rows:
        norm = extract_normalization(row["raw_json"])
        quality_score = float(norm.get("market_quality_score") or 0)
        quality_grade = norm.get("market_quality_grade") or "D"
        subtype = norm.get("subtype") or "unknown"
        normalized_category = norm.get("normalized_category") or "unknown"

        if subtype == "multi_leg_bundle":
            quality_score -= 30

        if row["yes_price"] is not None and 5 <= row["yes_price"] <= 95:
            quality_score += 15

        if row["volume"]:
            quality_score += min(float(row["volume"]) / 1000 * 10, 10)

        if row["open_interest"]:
            quality_score += min(float(row["open_interest"]) / 1000 * 10, 10)

        scored.append(
            {
                "ticker": row["ticker"],
                "yes_price": row["yes_price"],
                "volume": row["volume"],
                "open_interest": row["open_interest"],
                "quality_score": quality_score,
                "quality_grade": quality_grade,
                "subtype": subtype,
                "category": normalized_category,
            }
        )

    scored.sort(
        key=lambda item: (
            item["quality_score"],
            item["open_interest"] or 0,
            item["volume"] or 0,
        ),
        reverse=True,
    )

    selected = scored[:limit]

    print(f"Markets currently in database: {total_markets}")
    print(f"Useful priced markets available: {useful_markets}")
    print("Selected markets for orderbook snapshots:")

    for item in selected:
        print(
            f"- {item['ticker']} | "
            f"Q {round(item['quality_score'], 2)} | "
            f"{item['quality_grade']} | "
            f"{item['category']} | "
            f"{item['subtype']} | "
            f"YES {item['yes_price']} | "
            f"VOL {item['volume']} | "
            f"OI {item['open_interest']}"
        )

    return [item["ticker"] for item in selected]


def fetch_orderbook(ticker: str) -> Optional[Dict[str, Any]]:
    url = f"{KALSHI_BASE_URL}/markets/{ticker}/orderbook"

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 404:
            print(f"Orderbook not found: {ticker}")
            return None

        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"Orderbook error for {ticker}: {e}")
        return None


def parse_orderbook_levels(levels: Any) -> Tuple[Optional[float], float]:
    if not levels:
        return None, 0.0

    best_price = None
    total_depth = 0.0

    for level in levels:
        price = None
        size = 0.0

        if isinstance(level, dict):
            price = (
                level.get("price")
                or level.get("price_dollars")
                or level.get("yes_price")
                or level.get("no_price")
            )
            size = (
                level.get("size")
                or level.get("quantity")
                or level.get("contracts")
                or 0
            )

        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            price = level[0]
            size = level[1]

        try:
            price = float(price) * 100 if price is not None and float(price) <= 1 else float(price)
            size = float(size or 0)
        except (TypeError, ValueError):
            continue

        total_depth += size

        if best_price is None:
            best_price = price
        elif price is not None:
            best_price = max(best_price, price)

    return best_price, total_depth


def extract_orderbook_values(raw: Dict[str, Any]) -> Dict[str, Any]:
    orderbook = raw.get("orderbook_fp") or raw.get("orderbook") or raw

    yes_levels = (
        orderbook.get("yes_dollars")
        or orderbook.get("yes")
        or orderbook.get("yes_bids")
        or []
    )

    no_levels = (
        orderbook.get("no_dollars")
        or orderbook.get("no")
        or orderbook.get("no_bids")
        or []
    )

    best_yes_bid, yes_bid_depth = parse_orderbook_levels(yes_levels)
    best_no_bid, no_bid_depth = parse_orderbook_levels(no_levels)

    best_yes_ask = None
    best_no_ask = None

    if best_no_bid is not None:
        best_yes_ask = 100 - best_no_bid

    if best_yes_bid is not None:
        best_no_ask = 100 - best_yes_bid

    spread = None
    if best_yes_bid is not None and best_yes_ask is not None:
        spread = best_yes_ask - best_yes_bid

    total_depth = yes_bid_depth + no_bid_depth
    order_imbalance = None

    if total_depth > 0:
        order_imbalance = (yes_bid_depth - no_bid_depth) / total_depth

    return {
        "best_yes_bid": best_yes_bid,
        "best_yes_ask": best_yes_ask,
        "best_no_bid": best_no_bid,
        "best_no_ask": best_no_ask,
        "spread": spread,
        "yes_bid_depth": yes_bid_depth,
        "yes_ask_depth": 0.0,
        "no_bid_depth": no_bid_depth,
        "no_ask_depth": 0.0,
        "order_imbalance": order_imbalance,
    }


def save_orderbook_snapshot(ticker: str, raw: Dict[str, Any]) -> bool:
    values = extract_orderbook_values(raw)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO order_book_snapshots (
            ticker,
            best_yes_bid,
            best_yes_ask,
            best_no_bid,
            best_no_ask,
            spread,
            yes_bid_depth,
            yes_ask_depth,
            no_bid_depth,
            no_ask_depth,
            order_imbalance,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            values["best_yes_bid"],
            values["best_yes_ask"],
            values["best_no_bid"],
            values["best_no_ask"],
            values["spread"],
            values["yes_bid_depth"],
            values["yes_ask_depth"],
            values["no_bid_depth"],
            values["no_ask_depth"],
            values["order_imbalance"],
            json.dumps(raw, sort_keys=True),
        ),
    )

    conn.commit()
    conn.close()

    return True


def collect_orderbook_snapshots(limit: int = 25) -> int:
    tickers = fetch_active_tickers(limit=limit)

    print(f"Collecting order books for {len(tickers)} markets...")

    saved = 0

    for ticker in tickers:
        raw = fetch_orderbook(ticker)

        if raw is None:
            continue

        save_orderbook_snapshot(ticker, raw)
        saved += 1

        print(f"Saved orderbook snapshot: {ticker}")

        time.sleep(0.15)

    print("Order book snapshot collection complete.")
    print(f"Snapshots saved: {saved}")

    return saved


if __name__ == "__main__":
    collect_orderbook_snapshots()