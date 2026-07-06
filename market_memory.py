import json
import os
import time

MEMORY_FILE = "market_memory.json"
MAX_AGE_SECONDS = 60 * 60 * 2


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def prune_old(records):
    now = time.time()
    return [
        r for r in records
        if now - r.get("timestamp", 0) <= MAX_AGE_SECONDS
    ]


def remember_market(ticker, price, volume_24h, bid=None, ask=None):
    memory = load_memory()
    ticker = str(ticker).upper()

    records = memory.get(ticker, [])
    records = prune_old(records)

    records.append({
        "timestamp": time.time(),
        "price": float(price or 0),
        "volume_24h": float(volume_24h or 0),
        "bid": float(bid or 0),
        "ask": float(ask or 0),
    })

    memory[ticker] = records
    save_memory(memory)


def get_window_volume(ticker, window_seconds=300):
    memory = load_memory()
    ticker = str(ticker).upper()
    records = memory.get(ticker, [])

    if len(records) < 2:
        return {
            "valid": False,
            "window_volume": 0,
            "reason": "Not enough local history yet",
        }

    now = time.time()
    recent = records[-1]

    old_candidates = [
        r for r in records
        if now - r.get("timestamp", 0) >= window_seconds
    ]

    if not old_candidates:
        return {
            "valid": False,
            "window_volume": 0,
            "reason": "Need more time to build 5m volume",
        }

    old = old_candidates[-1]

    volume_diff = recent.get("volume_24h", 0) - old.get("volume_24h", 0)

    if volume_diff < 0:
        volume_diff = 0

    return {
        "valid": True,
        "window_volume": round(volume_diff, 2),
        "reason": "Calculated from local 5m memory",
    }


def get_price_change(ticker, window_seconds=300):
    memory = load_memory()
    ticker = str(ticker).upper()
    records = memory.get(ticker, [])

    if len(records) < 2:
        return {
            "valid": False,
            "price_change": 0,
            "reason": "Not enough local history yet",
        }

    now = time.time()
    recent = records[-1]

    old_candidates = [
        r for r in records
        if now - r.get("timestamp", 0) >= window_seconds
    ]

    if not old_candidates:
        return {
            "valid": False,
            "price_change": 0,
            "reason": "Need more time to build 5m price change",
        }

    old = old_candidates[-1]

    price_change = recent.get("price", 0) - old.get("price", 0)

    return {
        "valid": True,
        "price_change": round(price_change, 2),
        "reason": "Calculated from local 5m memory",
    }


if __name__ == "__main__":
    remember_market(
        ticker="TEST",
        price=42,
        volume_24h=1000,
        bid=41,
        ask=43,
    )

    print(get_window_volume("TEST"))
    print(get_price_change("TEST"))