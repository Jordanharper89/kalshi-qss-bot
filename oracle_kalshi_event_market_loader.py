"""
ORACLE-039.6 — Kalshi Event Market Loader

Purpose:
- Pull Kalshi events first
- Use event_ticker to fetch real markets attached to events
- Avoid newest provisional/MVE combo market trap
- Save useful markets into oracle_market_universe.json

Safe:
- No trading
- No orders
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


def get_dollar(raw, *keys):
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return safe_float(value)
    return 0.0


def normalize_market(raw, event=None):
    raw = raw or {}
    event = event or {}

    ticker = raw.get("ticker") or raw.get("market_ticker") or "UNKNOWN"
    title = raw.get("title") or raw.get("subtitle") or event.get("title") or ticker

    yes_bid = get_dollar(raw, "yes_bid_dollars", "yes_bid")
    yes_ask = get_dollar(raw, "yes_ask_dollars", "yes_ask")
    no_bid = get_dollar(raw, "no_bid_dollars", "no_bid")
    no_ask = get_dollar(raw, "no_ask_dollars", "no_ask")
    last_price = get_dollar(raw, "last_price_dollars", "last_price")
    previous_price = get_dollar(raw, "previous_price_dollars", "previous_price")

    volume = get_dollar(raw, "volume_dollars", "volume")
    volume_24h = get_dollar(raw, "volume_24h_dollars", "volume_24h")
    liquidity = get_dollar(raw, "liquidity_dollars", "liquidity")
    open_interest = get_dollar(raw, "open_interest", "open_interest_fp")

    market_price = last_price or yes_ask or yes_bid or previous_price or 0

    return {
        "ticker": str(ticker).upper(),
        "title": str(title),
        "event_title": event.get("title"),
        "category": raw.get("category") or event.get("category") or "unknown",
        "status": raw.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "last_price": last_price,
        "previous_price": previous_price,
        "market_price": market_price,
        "volume": volume,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "open_interest": open_interest,
        "close_time": raw.get("close_time"),
        "expiration_time": raw.get("expiration_time"),
        "event_ticker": raw.get("event_ticker") or event.get("event_ticker"),
        "series_ticker": event.get("series_ticker"),
        "source": "kalshi_event_loader",
        "raw": raw,
        "event": event,
        "seen_at": now(),
    }


def is_bad_market(raw):
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


def activity_score(m):
    return (
        m.get("volume", 0) * 1.0
        + m.get("volume_24h", 0) * 2.0
        + m.get("liquidity", 0) * 1.5
        + m.get("open_interest", 0) * 0.5
        + max(
            m.get("yes_bid", 0),
            m.get("yes_ask", 0),
            m.get("no_bid", 0),
            m.get("no_ask", 0),
            m.get("last_price", 0),
            m.get("previous_price", 0),
        ) * 100
    )


def fetch_events(max_pages=10, page_limit=200):
    events = []
    cursor = None

    for _ in range(max_pages):
        params = {"limit": page_limit}
        if cursor:
            params["cursor"] = cursor

        r = requests.get(f"{BASE_URL}/events", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        batch = data.get("events", [])
        events.extend(batch)

        cursor = data.get("cursor")
        if not cursor:
            break

    return events


def fetch_event_detail(event_ticker):
    r = requests.get(f"{BASE_URL}/events/{event_ticker}", timeout=20)
    r.raise_for_status()
    return r.json()


def extract_markets_from_event_detail(detail):
    if not isinstance(detail, dict):
        return []

    if isinstance(detail.get("markets"), list):
        return detail.get("markets")

    event = detail.get("event")
    if isinstance(event, dict) and isinstance(event.get("markets"), list):
        return event.get("markets")

    return []


def refresh_universe(max_events=100, min_activity=False):
    events = fetch_events(max_pages=10, page_limit=200)[:int(max_events)]

    kept = []
    rejected = {
        "events_seen": len(events),
        "events_with_markets": 0,
        "bad_market": 0,
        "no_price": 0,
        "no_activity": 0,
        "errors": 0,
    }

    for event in events:
        event_ticker = event.get("event_ticker")
        if not event_ticker:
            continue

        try:
            detail = fetch_event_detail(event_ticker)
            markets = extract_markets_from_event_detail(detail)

            if markets:
                rejected["events_with_markets"] += 1

            for raw in markets:
                if is_bad_market(raw):
                    rejected["bad_market"] += 1
                    continue

                m = normalize_market(raw, event=event)

                price = max(
                    m["yes_bid"],
                    m["yes_ask"],
                    m["no_bid"],
                    m["no_ask"],
                    m["last_price"],
                    m["previous_price"],
                )

                activity = max(
                    m["volume"],
                    m["volume_24h"],
                    m["liquidity"],
                    m["open_interest"],
                )

                if price <= 0:
                    rejected["no_price"] += 1
                    continue

                if min_activity and activity <= 0:
                    rejected["no_activity"] += 1
                    continue

                m["activity_score"] = round(activity_score(m), 4)
                kept.append(m)

        except Exception as e:
            rejected["errors"] += 1
            print(f"[ORACLE-039.6] event {event_ticker} error: {e}")

    deduped = {}
    for m in kept:
        deduped[m["ticker"]] = m

    markets = list(deduped.values())
    markets.sort(key=lambda x: x.get("activity_score", 0), reverse=True)

    payload = {
        "version": "ORACLE-039.6",
        "updated_at": now(),
        "count": len(markets),
        "rejected": rejected,
        "markets": markets,
    }

    UNIVERSE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_markets(limit=200):
    if not UNIVERSE_FILE.exists():
        refresh_universe(max_events=100)

    data = json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
    return data.get("markets", [])[:int(limit)]


def diagnostics():
    data = refresh_universe(max_events=100, min_activity=False)

    return {
        "module": "oracle_kalshi_event_market_loader",
        "status": "ok",
        "markets_loaded": data.get("count"),
        "rejected": data.get("rejected"),
        "top": data.get("markets", [])[:5],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
