"""
ORACLE-039.4 — Market Universe Filter

Purpose:
- Filter raw Kalshi market universe into useful research candidates
- Remove zero-price / zero-volume junk
- Reduce provisional combo/MVE noise
- Sort by activity, liquidity, and tradability

Safe:
- No trading
- No orders
"""

import json
import time
from pathlib import Path
from math import isfinite

RAW_FILE = Path("oracle_market_universe.json")
FILTERED_FILE = Path("oracle_market_universe_filtered.json")


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


def is_combo_market(market):
    ticker = str(market.get("ticker", "")).upper()
    raw = market.get("raw", {}) if isinstance(market.get("raw"), dict) else {}

    if "KXMVE" in ticker:
        return True

    if raw.get("mve_collection_ticker"):
        return True

    if raw.get("mve_selected_legs"):
        return True

    return False


def is_provisional(market):
    raw = market.get("raw", {}) if isinstance(market.get("raw"), dict) else {}
    return bool(raw.get("is_provisional"))


def market_activity_score(market):
    volume = safe_float(market.get("volume"))
    volume_24h = safe_float(market.get("volume_24h"))
    open_interest = safe_float(market.get("open_interest"))
    yes_bid = safe_float(market.get("yes_bid"))
    yes_ask = safe_float(market.get("yes_ask"))
    no_bid = safe_float(market.get("no_bid"))
    no_ask = safe_float(market.get("no_ask"))
    last_price = safe_float(market.get("last_price"))

    price_signal = max(yes_bid, yes_ask, no_bid, no_ask, last_price)

    return (
        volume * 1.0
        + volume_24h * 2.0
        + open_interest * 0.5
        + price_signal * 100.0
    )


def is_tradable_candidate(market, allow_combo=False):
    status = str(market.get("status", "")).lower()

    if status not in ("active", "open"):
        return False

    if is_provisional(market):
        return False

    if not allow_combo and is_combo_market(market):
        return False

    yes_bid = safe_float(market.get("yes_bid"))
    yes_ask = safe_float(market.get("yes_ask"))
    no_bid = safe_float(market.get("no_bid"))
    no_ask = safe_float(market.get("no_ask"))
    last_price = safe_float(market.get("last_price"))
    volume = safe_float(market.get("volume"))
    volume_24h = safe_float(market.get("volume_24h"))
    open_interest = safe_float(market.get("open_interest"))

    has_price = max(yes_bid, yes_ask, no_bid, no_ask, last_price) > 0
    has_activity = max(volume, volume_24h, open_interest) > 0

    if not has_price:
        return False

    if not has_activity:
        return False

    return True


def load_raw_markets():
    if not RAW_FILE.exists():
        return []

    try:
        data = json.loads(RAW_FILE.read_text(encoding="utf-8"))
        markets = data.get("markets", [])
        return markets if isinstance(markets, list) else []
    except Exception:
        return []


def filter_markets(limit=250, allow_combo=False):
    raw = load_raw_markets()

    kept = []
    rejected = {
        "total_raw": len(raw),
        "bad_status": 0,
        "provisional": 0,
        "combo": 0,
        "no_price": 0,
        "no_activity": 0,
    }

    for market in raw:
        status = str(market.get("status", "")).lower()

        if status not in ("active", "open"):
            rejected["bad_status"] += 1
            continue

        if is_provisional(market):
            rejected["provisional"] += 1
            continue

        if not allow_combo and is_combo_market(market):
            rejected["combo"] += 1
            continue

        yes_bid = safe_float(market.get("yes_bid"))
        yes_ask = safe_float(market.get("yes_ask"))
        no_bid = safe_float(market.get("no_bid"))
        no_ask = safe_float(market.get("no_ask"))
        last_price = safe_float(market.get("last_price"))
        volume = safe_float(market.get("volume"))
        volume_24h = safe_float(market.get("volume_24h"))
        open_interest = safe_float(market.get("open_interest"))

        if max(yes_bid, yes_ask, no_bid, no_ask, last_price) <= 0:
            rejected["no_price"] += 1
            continue

        if max(volume, volume_24h, open_interest) <= 0:
            rejected["no_activity"] += 1
            continue

        market["activity_score"] = round(market_activity_score(market), 4)
        kept.append(market)

    kept.sort(key=lambda m: m.get("activity_score", 0), reverse=True)
    kept = kept[:int(limit)]

    payload = {
        "version": "ORACLE-039.4",
        "updated_at": now(),
        "count": len(kept),
        "rejected": rejected,
        "markets": kept,
    }

    FILTERED_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_filtered_markets(limit=100):
    if not FILTERED_FILE.exists():
        filter_markets(limit=limit)

    try:
        data = json.loads(FILTERED_FILE.read_text(encoding="utf-8"))
        markets = data.get("markets", [])
        return markets[:int(limit)]
    except Exception:
        return []


def diagnostics():
    payload = filter_markets(limit=250)

    return {
        "module": "oracle_market_universe_filter",
        "status": "ok",
        "kept": payload.get("count"),
        "rejected": payload.get("rejected"),
        "top": payload.get("markets", [])[:5],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
