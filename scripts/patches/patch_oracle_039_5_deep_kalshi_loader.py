from pathlib import Path

TARGET = Path("oracle_kalshi_public_loader.py")

TARGET.write_text(r'''
"""
ORACLE-039.5 — Deep Kalshi Public Loader

Purpose:
- Pull deeper Kalshi market universe
- Skip provisional/MVE combo markets while loading
- Save useful active markets into oracle_market_universe.json
"""

import json
import time
from pathlib import Path
from math import isfinite

import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
UNIVERSE_FILE = Path("oracle_market_universe.json")


def now():
    return time.time()


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if not isfinite(value):
            return default
        return value
    except Exception:
        return default


def is_combo_or_provisional(raw):
    ticker = str(raw.get("ticker", "")).upper()

    if raw.get("is_provisional"):
        return True
    if "KXMVE" in ticker:
        return True
    if raw.get("mve_collection_ticker"):
        return True
    if raw.get("mve_selected_legs"):
        return True

    return False


def normalize_market(raw):
    raw = raw or {}

    ticker = raw.get("ticker") or raw.get("market_ticker") or "UNKNOWN"
    title = raw.get("title") or raw.get("subtitle") or ticker

    yes_bid = safe_float(raw.get("yes_bid_dollars") or raw.get("yes_bid"))
    yes_ask = safe_float(raw.get("yes_ask_dollars") or raw.get("yes_ask"))
    no_bid = safe_float(raw.get("no_bid_dollars") or raw.get("no_bid"))
    no_ask = safe_float(raw.get("no_ask_dollars") or raw.get("no_ask"))
    last_price = safe_float(raw.get("last_price_dollars") or raw.get("last_price"))

    market_price = last_price or yes_ask or yes_bid or 0

    volume = safe_float(raw.get("volume_dollars") or raw.get("volume"))
    volume_24h = safe_float(raw.get("volume_24h_dollars") or raw.get("volume_24h"))
    liquidity = safe_float(raw.get("liquidity_dollars") or raw.get("liquidity"))
    open_interest = safe_float(raw.get("open_interest") or raw.get("open_interest_fp"))

    return {
        "ticker": str(ticker).upper(),
        "title": str(title),
        "category": raw.get("category") or "unknown",
        "status": raw.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "last_price": last_price,
        "market_price": market_price,
        "volume": volume,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "open_interest": open_interest,
        "close_time": raw.get("close_time"),
        "expiration_time": raw.get("expiration_time"),
        "event_ticker": raw.get("event_ticker"),
        "source": "kalshi_public",
        "raw": raw,
        "seen_at": now(),
    }


def activity_score(m):
    return (
        safe_float(m.get("volume")) * 1.0
        + safe_float(m.get("volume_24h")) * 2.0
        + safe_float(m.get("liquidity")) * 1.5
        + safe_float(m.get("open_interest")) * 0.5
        + max(
            safe_float(m.get("yes_bid")),
            safe_float(m.get("yes_ask")),
            safe_float(m.get("no_bid")),
            safe_float(m.get("no_ask")),
            safe_float(m.get("last_price")),
        ) * 100
    )


def fetch_active_markets(max_pages=25, page_limit=200, keep_limit=1000):
    kept = []
    rejected = {
        "combo_or_provisional": 0,
        "no_price": 0,
        "no_activity": 0,
        "raw_seen": 0,
        "pages": 0,
    }

    cursor = None

    for _ in range(max_pages):
        params = {
            "status": "open",
            "limit": page_limit,
        }

        if cursor:
            params["cursor"] = cursor

        r = requests.get(f"{BASE_URL}/markets", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        batch = data.get("markets", [])
        rejected["pages"] += 1
        rejected["raw_seen"] += len(batch)

        for raw in batch:
            if is_combo_or_provisional(raw):
                rejected["combo_or_provisional"] += 1
                continue

            m = normalize_market(raw)

            price = max(m["yes_bid"], m["yes_ask"], m["no_bid"], m["no_ask"], m["last_price"])
            activity = max(m["volume"], m["volume_24h"], m["liquidity"], m["open_interest"])

            if price <= 0:
                rejected["no_price"] += 1
                continue

            if activity <= 0:
                rejected["no_activity"] += 1
                continue

            m["activity_score"] = round(activity_score(m), 4)
            kept.append(m)

        cursor = data.get("cursor")
        if not cursor:
            break

        if len(kept) >= keep_limit:
            break

    kept.sort(key=lambda x: x.get("activity_score", 0), reverse=True)
    return kept[:keep_limit], rejected


def save_universe(markets, rejected):
    payload = {
        "version": "ORACLE-039.5",
        "updated_at": now(),
        "count": len(markets),
        "rejected": rejected,
        "markets": markets,
    }

    UNIVERSE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def refresh_universe():
    markets, rejected = fetch_active_markets()
    return save_universe(markets, rejected)


def get_markets(limit=200):
    if not UNIVERSE_FILE.exists():
        refresh_universe()

    data = json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
    return data.get("markets", [])[:int(limit)]


def diagnostics():
    data = refresh_universe()
    return {
        "module": "oracle_kalshi_public_loader",
        "status": "ok",
        "markets_loaded": data.get("count"),
        "rejected": data.get("rejected"),
        "top": data.get("markets", [])[:5],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-039.5 INSTALLED")
print(" Deep Kalshi Public Loader")
print("===================================")
print()
print("Test:")
print(" python oracle_kalshi_public_loader.py")