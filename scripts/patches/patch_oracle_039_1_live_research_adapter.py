from pathlib import Path

TARGET = Path("oracle_live_research_adapter.py")

TARGET.write_text(r'''
"""
ORACLE-039.1 — Live Research Adapter

Purpose:
- Pull real available Oracle/Kalshi opportunity data from existing modules
- Normalize different sources into one opportunity format
- Feed Continuous Intelligence with useful live candidates
- Avoid relying only on provider placeholders

Safe module:
- Does not execute trades
- Does not place orders
"""

import time
import importlib
from math import isfinite


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


def normalize_opportunity(raw, source="unknown"):
    raw = raw or {}

    ticker = (
        raw.get("ticker")
        or raw.get("market_ticker")
        or raw.get("symbol")
        or raw.get("id")
        or raw.get("event_ticker")
        or "UNKNOWN"
    )

    title = (
        raw.get("title")
        or raw.get("market_title")
        or raw.get("name")
        or raw.get("subtitle")
        or ticker
    )

    side = (
        raw.get("side")
        or raw.get("recommendation")
        or raw.get("decision")
        or raw.get("pick")
        or "WATCH"
    )

    edge = safe_float(
        raw.get("edge")
        or raw.get("edge_score")
        or raw.get("expected_edge")
        or raw.get("edge_pct")
        or raw.get("value_edge")
        or 0
    )

    confidence = safe_float(
        raw.get("confidence")
        or raw.get("confidence_score")
        or raw.get("probability_confidence")
        or raw.get("score")
        or 50
    )

    fair_value = safe_float(
        raw.get("fair_value")
        or raw.get("oracle_fair_value")
        or raw.get("fv")
        or raw.get("true_price")
        or raw.get("probability")
        or 0
    )

    market_price = safe_float(
        raw.get("market_price")
        or raw.get("price")
        or raw.get("yes_price")
        or raw.get("current_price")
        or raw.get("last_price")
        or raw.get("last_trade_price")
        or 0
    )

    volume = safe_float(
        raw.get("volume")
        or raw.get("volume_24h")
        or raw.get("liquidity")
        or raw.get("open_interest")
        or 0
    )

    age_seconds = safe_float(
        raw.get("age_seconds")
        or raw.get("data_age_seconds")
        or 0
    )

    providers = raw.get("providers")
    if not providers:
        providers = [source]

    return {
        "ticker": safe_text(ticker).upper(),
        "title": safe_text(title),
        "side": safe_text(side).upper(),
        "edge": edge,
        "confidence": confidence,
        "fair_value": fair_value,
        "market_price": market_price,
        "volume": volume,
        "age_seconds": age_seconds,
        "providers": providers,
        "source": source,
        "raw": raw,
        "seen_at": now(),
    }


def _dedupe(items):
    deduped = {}
    for item in items:
        ticker = item.get("ticker", "UNKNOWN")
        if ticker == "UNKNOWN":
            continue

        old = deduped.get(ticker)
        if not old:
            deduped[ticker] = item
            continue

        old_score = safe_float(old.get("edge")) + safe_float(old.get("confidence")) / 10
        new_score = safe_float(item.get("edge")) + safe_float(item.get("confidence")) / 10

        if new_score > old_score:
            deduped[ticker] = item

    return list(deduped.values())


def _load_from_research_engine():
    results = []

    try:
        from oracle_research_engine import oracle_research_engine

        if hasattr(oracle_research_engine, "get_snapshot"):
            snap = oracle_research_engine.get_snapshot()

            if isinstance(snap, dict):
                for key in ("opportunities", "ranked", "signals", "markets", "top"):
                    value = snap.get(key)
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                results.append(normalize_opportunity(item, source=f"research_engine.{key}"))

    except Exception as e:
        print(f"[ORACLE-039.1] research engine load error: {e}")

    return results


def _load_from_opportunity_feed():
    results = []

    try:
        from oracle_opportunity_feed import build_oracle_opportunity_feed

        try:
            feed = build_oracle_opportunity_feed(
                watched_markets=[],
                min_grade="C",
                min_edge=0,
                min_confidence=0,
                max_items=50,
            )
        except TypeError:
            feed = build_oracle_opportunity_feed()

        if isinstance(feed, list):
            for item in feed:
                if isinstance(item, dict):
                    results.append(normalize_opportunity(item, source="opportunity_feed"))

    except Exception as e:
        print(f"[ORACLE-039.1] opportunity feed load error: {e}")

    return results


def _load_from_market_cache():
    results = []

    try:
        from oracle_market_cache import oracle_market_cache

        candidates = []

        for method_name in ("get_all", "list_all", "all_markets", "get_markets", "snapshot"):
            method = getattr(oracle_market_cache, method_name, None)
            if callable(method):
                try:
                    value = method()
                    if isinstance(value, list):
                        candidates = value
                        break
                    if isinstance(value, dict):
                        for key in ("markets", "items", "data", "results"):
                            if isinstance(value.get(key), list):
                                candidates = value.get(key)
                                break
                except Exception:
                    continue

        if isinstance(candidates, list):
            for item in candidates[:200]:
                if isinstance(item, dict):
                    results.append(normalize_opportunity(item, source="market_cache"))

    except Exception as e:
        print(f"[ORACLE-039.1] market cache load error: {e}")

    return results


def _load_from_watchlist():
    results = []

    try:
        import json
        from pathlib import Path

        path = Path("oracle_watchlist.json")
        if not path.exists():
            return results

        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, dict):
            data = list(data.values())

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    results.append(normalize_opportunity(item, source="watchlist"))
                else:
                    results.append(normalize_opportunity({"ticker": item, "title": item}, source="watchlist"))

    except Exception as e:
        print(f"[ORACLE-039.1] watchlist load error: {e}")

    return results


def get_live_opportunities(limit=100):
    """
    Main entry point for the continuous intelligence system.
    """
    items = []

    loaders = [
        _load_from_research_engine,
        _load_from_opportunity_feed,
        _load_from_market_cache,
        _load_from_watchlist,
    ]

    for loader in loaders:
        try:
            items.extend(loader())
        except Exception as e:
            print(f"[ORACLE-039.1] loader error {loader.__name__}: {e}")

    items = _dedupe(items)

    items.sort(
        key=lambda x: (
            safe_float(x.get("edge")),
            safe_float(x.get("confidence")),
            safe_float(x.get("volume")),
        ),
        reverse=True,
    )

    return items[:int(limit)]


def diagnostics():
    items = get_live_opportunities(limit=20)

    return {
        "module": "oracle_live_research_adapter",
        "status": "ok",
        "opportunities": len(items),
        "top": items[:3],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-039.1 INSTALLED")
print(" Live Research Adapter")
print("===================================")
print()
print("Created:")
print(" oracle_live_research_adapter.py")
print()
print("Test:")
print(" python oracle_live_research_adapter.py")