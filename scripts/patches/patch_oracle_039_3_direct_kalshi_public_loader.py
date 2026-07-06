from pathlib import Path

TARGET = Path("oracle_kalshi_public_loader.py")

TARGET.write_text(r'''
"""
ORACLE-039.3 — Direct Kalshi Public Market Loader

Purpose:
- Pull open Kalshi markets directly from the public Trade API
- Save them into oracle_market_universe.json
- Feed Oracle with real market candidates

Safe:
- No trading
- No orders
- No auth required
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


def normalize_market(raw):
    raw = raw or {}

    ticker = raw.get("ticker") or raw.get("market_ticker") or "UNKNOWN"
    title = raw.get("title") or raw.get("subtitle") or ticker

    yes_bid = safe_float(raw.get("yes_bid"))
    yes_ask = safe_float(raw.get("yes_ask"))
    last_price = safe_float(raw.get("last_price"))

    market_price = last_price or yes_ask or yes_bid or 0

    return {
        "ticker": str(ticker).upper(),
        "title": str(title),
        "category": raw.get("category") or "unknown",
        "status": raw.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": safe_float(raw.get("no_bid")),
        "no_ask": safe_float(raw.get("no_ask")),
        "last_price": last_price,
        "market_price": market_price,
        "volume": safe_float(raw.get("volume")),
        "volume_24h": safe_float(raw.get("volume_24h")),
        "open_interest": safe_float(raw.get("open_interest")),
        "close_time": raw.get("close_time"),
        "expiration_time": raw.get("expiration_time"),
        "event_ticker": raw.get("event_ticker"),
        "source": "kalshi_public",
        "raw": raw,
        "seen_at": now(),
    }


def fetch_open_markets(limit=1000):
    markets = []
    cursor = None

    while len(markets) < limit:
        params = {
            "status": "open",
            "limit": min(200, limit - len(markets)),
        }

        if cursor:
            params["cursor"] = cursor

        r = requests.get(f"{BASE_URL}/markets", params=params, timeout=15)
        r.raise_for_status()

        data = r.json()
        batch = data.get("markets", [])

        if not batch:
            break

        markets.extend(batch)

        cursor = data.get("cursor")
        if not cursor:
            break

    return [normalize_market(m) for m in markets]


def save_universe(markets):
    payload = {
        "version": "ORACLE-039.3",
        "updated_at": now(),
        "count": len(markets),
        "markets": markets,
    }

    UNIVERSE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def refresh_universe(limit=1000):
    markets = fetch_open_markets(limit=limit)
    return save_universe(markets)


def get_markets(limit=200):
    if not UNIVERSE_FILE.exists():
        refresh_universe(limit=limit)

    data = json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
    return data.get("markets", [])[:int(limit)]


def diagnostics():
    data = refresh_universe(limit=500)

    return {
        "module": "oracle_kalshi_public_loader",
        "status": "ok",
        "markets_loaded": data.get("count"),
        "top": data.get("markets", [])[:5],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-039.3 INSTALLED")
print(" Direct Kalshi Public Loader")
print("===================================")
print()
print("Created:")
print(" oracle_kalshi_public_loader.py")
print()
print("Test:")
print(" python oracle_kalshi_public_loader.py")