from pathlib import Path

TARGET = Path("oracle_kalshi_market_universe.py")

TARGET.write_text(r'''
"""
ORACLE-039.2 — Kalshi Market Universe Loader

Purpose:
- Pull live/available Kalshi markets from existing repo modules when possible
- Normalize markets into one Oracle-friendly format
- Save universe to oracle_market_universe.json
- Give Oracle live candidates instead of only watchlist/test markets

Safe module:
- Does not execute trades
- Does not place orders
"""

import json
import time
import importlib
from pathlib import Path
from math import isfinite

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


def safe_text(value, default=""):
    if value is None:
        return default
    return str(value)


def normalize_market(raw, source="kalshi"):
    raw = raw or {}

    ticker = (
        raw.get("ticker")
        or raw.get("market_ticker")
        or raw.get("id")
        or raw.get("symbol")
        or "UNKNOWN"
    )

    title = (
        raw.get("title")
        or raw.get("market_title")
        or raw.get("name")
        or raw.get("subtitle")
        or ticker
    )

    yes_price = safe_float(
        raw.get("yes_price")
        or raw.get("yes_bid")
        or raw.get("last_price")
        or raw.get("price")
        or raw.get("current_price")
        or 0
    )

    no_price = safe_float(
        raw.get("no_price")
        or raw.get("no_bid")
        or 0
    )

    volume = safe_float(
        raw.get("volume")
        or raw.get("volume_24h")
        or raw.get("liquidity")
        or raw.get("open_interest")
        or 0
    )

    status = safe_text(raw.get("status") or raw.get("state") or "unknown").lower()

    return {
        "ticker": safe_text(ticker).upper(),
        "title": safe_text(title),
        "category": safe_text(raw.get("category") or raw.get("event_type") or "unknown"),
        "status": status,
        "yes_price": yes_price,
        "no_price": no_price,
        "market_price": yes_price,
        "volume": volume,
        "open_interest": safe_float(raw.get("open_interest") or 0),
        "close_time": raw.get("close_time") or raw.get("expiration_time") or raw.get("close_ts"),
        "source": source,
        "raw": raw,
        "seen_at": now(),
    }


def _extract_markets(value):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]

    if isinstance(value, dict):
        for key in ("markets", "items", "data", "results"):
            if isinstance(value.get(key), list):
                return [x for x in value.get(key) if isinstance(x, dict)]

    return []


def _try_module_function(module_name, function_names):
    markets = []

    try:
        module = importlib.import_module(module_name)
    except Exception:
        return markets

    for fn_name in function_names:
        fn = getattr(module, fn_name, None)

        if not callable(fn):
            continue

        try:
            try:
                value = fn()
            except TypeError:
                value = fn(limit=200)

            markets = _extract_markets(value)

            if markets:
                print(f"[ORACLE-039.2] Loaded {len(markets)} markets from {module_name}.{fn_name}")
                return markets

        except Exception as e:
            print(f"[ORACLE-039.2] {module_name}.{fn_name} failed: {e}")

    return markets


def load_from_existing_modules():
    candidates = [
        ("kalshi_market_api", ["get_markets", "list_markets", "fetch_markets"]),
        ("kalshi_api", ["get_markets", "list_markets", "fetch_markets"]),
        ("kalshi_client", ["get_markets", "list_markets", "fetch_markets"]),
        ("market_data_service", ["get_markets", "list_markets", "snapshot"]),
        ("market_cache", ["get_markets", "list_markets", "get_all"]),
        ("oracle_market_cache", ["get_markets", "list_markets", "get_all", "snapshot"]),
    ]

    all_markets = []

    for module_name, functions in candidates:
        markets = _try_module_function(module_name, functions)
        if markets:
            all_markets.extend(markets)

    return all_markets


def dedupe(markets):
    out = {}

    for item in markets:
        m = normalize_market(item)
        ticker = m.get("ticker")

        if ticker and ticker != "UNKNOWN":
            out[ticker] = m

    return list(out.values())


def save_universe(markets):
    payload = {
        "version": "ORACLE-039.2",
        "updated_at": now(),
        "count": len(markets),
        "markets": markets,
    }

    UNIVERSE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_universe():
    if not UNIVERSE_FILE.exists():
        return {
            "version": "ORACLE-039.2",
            "updated_at": None,
            "count": 0,
            "markets": [],
        }

    try:
        return json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "version": "ORACLE-039.2",
            "updated_at": None,
            "count": 0,
            "markets": [],
            "error": "failed_to_load",
        }


def refresh_universe():
    raw = load_from_existing_modules()
    markets = dedupe(raw)
    return save_universe(markets)


def get_markets(limit=200):
    data = load_universe()
    markets = data.get("markets", [])
    return markets[:int(limit)]


def diagnostics():
    data = refresh_universe()

    return {
        "module": "oracle_kalshi_market_universe",
        "status": "ok",
        "markets_loaded": data.get("count", 0),
        "file": str(UNIVERSE_FILE),
        "top": data.get("markets", [])[:3],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-039.2 INSTALLED")
print(" Kalshi Market Universe Loader")
print("===================================")
print()
print("Created:")
print(" oracle_kalshi_market_universe.py")
print()
print("Test:")
print(" python oracle_kalshi_market_universe.py")