import json
import re
import requests

from oracle.database.db import get_connection, init_db
from oracle.collectors.kalshi.market_collector import dollars_to_cents, fp_to_number, safe_get
from oracle.collectors.kalshi.orderbook_collector import fetch_orderbook, save_orderbook_snapshot
from oracle.engines.features import save_features
from oracle.engines.signal_engine import save_signal
from oracle.engines.market_normalizer import (
    classify_category,
    classify_subtype,
    score_market_quality,
    grade_quality,
)


KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


def extract_oracle_ticker(value: str) -> str:
    text = value.strip()

    match = re.search(r"op_market_ticker=([A-Z0-9.\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r"ticker=([A-Z0-9.\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r"(KX[A-Z0-9.\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return text.upper()


def fetch_market_by_ticker(ticker: str):
    url = f"{KALSHI_BASE_URL}/markets/{ticker}"
    response = requests.get(url, timeout=20)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    data = response.json()
    return data.get("market") or data


def save_single_market(market: dict) -> bool:
    init_db()

    ticker = safe_get(market, "ticker")
    if not ticker:
        return False

    yes_ask = dollars_to_cents(market.get("yes_ask_dollars"))
    no_ask = dollars_to_cents(market.get("no_ask_dollars"))
    last_price = dollars_to_cents(market.get("last_price_dollars"))

    yes_price = yes_ask if yes_ask is not None else last_price
    no_price = no_ask

    conn = get_connection()
    cursor = conn.cursor()

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
            safe_get(market, "title", default=""),
            safe_get(market, "market_type", "event_ticker", default="unknown"),
            safe_get(market, "close_time", "expiration_time", "expected_expiration_time", default=None),
            safe_get(market, "status", default="unknown"),
            yes_price,
            no_price,
            fp_to_number(safe_get(market, "volume_fp", "volume_24h_fp", default=0)),
            fp_to_number(safe_get(market, "open_interest_fp", default=0)),
            json.dumps(market, sort_keys=True),
        ),
    )

    conn.commit()
    conn.close()
    return True


def normalize_single_market(ticker: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticker, market_title, category, yes_price, volume, open_interest, raw_json
        FROM markets
        WHERE ticker = ?
        LIMIT 1
        """,
        (ticker,),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    title = row["market_title"] or ""
    raw_category = row["category"] or ""

    normalized_category = classify_category(title, ticker, raw_category)
    subtype = classify_subtype(title)

    quality_score = score_market_quality(
        row["yes_price"],
        row["volume"],
        row["open_interest"],
        normalized_category,
        subtype,
    )

    quality_grade = grade_quality(quality_score)

    raw = {}
    try:
        raw = json.loads(row["raw_json"] or "{}")
    except Exception:
        raw = {}

    raw["oracle_normalization"] = {
        "normalized_category": normalized_category,
        "subtype": subtype,
        "market_quality_score": quality_score,
        "market_quality_grade": quality_grade,
    }

    cursor.execute(
        """
        UPDATE markets
        SET raw_json = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticker = ?
        """,
        (json.dumps(raw, sort_keys=True), ticker),
    )

    conn.commit()
    conn.close()


def build_feature_for_ticker(ticker: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM order_book_snapshots
        WHERE ticker = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (ticker,),
    )

    snapshot = cursor.fetchone()
    conn.close()

    if not snapshot:
        return False

    save_features(snapshot)
    return True


def build_signal_for_ticker(ticker: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            f.ticker,
            f.market_probability,
            f.liquidity_score,
            f.spread_score,
            f.order_book_imbalance,
            f.market_efficiency_score,
            m.market_title,
            m.yes_price,
            m.no_price,
            m.volume,
            m.open_interest,
            m.expiration_time,
            m.raw_json
        FROM features f
        JOIN markets m ON m.ticker = f.ticker
        WHERE f.ticker = ?
        ORDER BY f.id DESC
        LIMIT 1
        """,
        (ticker,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    save_signal(row)
    return True


def ensure_ticker_in_oracle(value: str) -> str:
    ticker = extract_oracle_ticker(value)

    print(f"Instant Oracle research requested for: {ticker}")

    market = fetch_market_by_ticker(ticker)

    if market:
        save_single_market(market)
        print(f"Market saved: {ticker}")
    else:
        print(f"Market fetch failed or not found: {ticker}")

    normalize_single_market(ticker)

    raw_orderbook = fetch_orderbook(ticker)

    if raw_orderbook:
        save_orderbook_snapshot(ticker, raw_orderbook)
        print(f"Orderbook saved: {ticker}")
    else:
        print(f"No orderbook returned for: {ticker}")

    feature_ok = build_feature_for_ticker(ticker)
    print(f"Feature built for {ticker}: {feature_ok}")

    signal_ok = build_signal_for_ticker(ticker)
    print(f"Signal built for {ticker}: {signal_ok}")

    return ticker