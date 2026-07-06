from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path.rename(path.with_suffix(path.suffix + f".bak_{stamp}"))

target = ROOT / "oracle_market_memory.py"
backup(target)

target.write_text(r'''
"""
ORACLE-029 — Market Memory Engine

Purpose:
- Save every market Oracle analyzes
- Store a timeline of snapshots per ticker
- Track edge, confidence, fair value, market price, recommendation, grade, risk
- Build Oracle's historical dataset for future self-learning
- Safe module: does not execute trades
"""

import json
import time
import threading
from pathlib import Path
from math import isfinite

MEMORY_FILE = Path("oracle_market_memory.json")
MAX_EVENTS_PER_MARKET = 500

_memory_lock = threading.Lock()


def _now():
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


def load_memory():
    if not MEMORY_FILE.exists():
        return {
            "version": "ORACLE-029",
            "created_at": _now(),
            "updated_at": _now(),
            "markets": {},
        }

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("memory root is not dict")

        data.setdefault("version", "ORACLE-029")
        data.setdefault("created_at", _now())
        data.setdefault("updated_at", _now())
        data.setdefault("markets", {})

        if not isinstance(data["markets"], dict):
            data["markets"] = {}

        return data

    except Exception:
        return {
            "version": "ORACLE-029",
            "created_at": _now(),
            "updated_at": _now(),
            "markets": {},
            "load_error": True,
        }


def save_memory(data):
    data["updated_at"] = _now()
    MEMORY_FILE.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def normalize_market(raw):
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
        or ticker
    )

    category = (
        raw.get("category")
        or raw.get("market_category")
        or raw.get("event_type")
        or "unknown"
    )

    return {
        "ticker": safe_text(ticker).upper(),
        "title": safe_text(title),
        "category": safe_text(category, "unknown"),
        "raw": raw,
    }


def normalize_event(raw, source="oracle"):
    raw = raw or {}

    scorecard = raw.get("scorecard") if isinstance(raw.get("scorecard"), dict) else raw

    return {
        "timestamp": _now(),
        "source": source,
        "side": safe_text(
            scorecard.get("side")
            or raw.get("side")
            or raw.get("recommendation")
            or "WATCH"
        ).upper(),
        "fair_value": safe_float(
            scorecard.get("fair_value")
            or raw.get("fair_value")
            or raw.get("oracle_fair_value")
            or raw.get("fv")
            or 0
        ),
        "market_price": safe_float(
            scorecard.get("market_price")
            or raw.get("market_price")
            or raw.get("price")
            or raw.get("yes_price")
            or raw.get("current_price")
            or 0
        ),
        "edge": safe_float(
            scorecard.get("edge")
            or raw.get("edge")
            or raw.get("edge_score")
            or raw.get("expected_edge")
            or 0
        ),
        "confidence": safe_float(
            scorecard.get("confidence")
            or raw.get("confidence")
            or raw.get("confidence_score")
            or 0
        ),
        "overall_score": safe_float(
            scorecard.get("overall_score")
            or raw.get("overall_score")
            or raw.get("score")
            or 0
        ),
        "grade": safe_text(
            scorecard.get("grade")
            or raw.get("grade")
            or "NA"
        ),
        "risk": safe_text(
            scorecard.get("risk")
            or raw.get("risk")
            or "NA"
        ),
        "reason": safe_text(
            scorecard.get("reason")
            or raw.get("reason")
            or ""
        ),
    }


def _new_market_record(market):
    now = _now()

    return {
        "ticker": market["ticker"],
        "title": market["title"],
        "category": market["category"],
        "first_seen": now,
        "last_seen": now,
        "events": [],
        "stats": {
            "event_count": 0,
            "highest_edge": 0,
            "lowest_edge": 0,
            "average_edge": 0,
            "average_confidence": 0,
            "highest_score": 0,
            "last_grade": "NA",
            "last_risk": "NA",
        },
        "outcome": {
            "resolved": False,
            "winner": None,
            "oracle_correct": None,
            "roi": None,
            "resolved_at": None,
        },
    }


def _recalculate_stats(record):
    events = record.get("events", [])
    if not events:
        return record

    edges = [safe_float(e.get("edge")) for e in events]
    confidences = [safe_float(e.get("confidence")) for e in events]
    scores = [safe_float(e.get("overall_score")) for e in events]

    record["stats"] = {
        "event_count": len(events),
        "highest_edge": round(max(edges), 4),
        "lowest_edge": round(min(edges), 4),
        "average_edge": round(sum(edges) / len(edges), 4),
        "average_confidence": round(sum(confidences) / len(confidences), 4),
        "highest_score": round(max(scores), 4),
        "last_grade": events[-1].get("grade", "NA"),
        "last_risk": events[-1].get("risk", "NA"),
    }

    return record


def remember_market(raw_market, source="oracle"):
    """
    Save one market snapshot.
    raw_market may be:
    - raw opportunity dict
    - intelligence scorecard dict
    - {"scorecard": scorecard}
    """
    market = normalize_market(raw_market)
    event = normalize_event(raw_market, source=source)

    ticker = market["ticker"]
    if not ticker or ticker == "UNKNOWN":
        return {
            "ok": False,
            "error": "missing_ticker",
        }

    with _memory_lock:
        data = load_memory()
        markets = data.setdefault("markets", {})

        if ticker not in markets:
            markets[ticker] = _new_market_record(market)

        record = markets[ticker]
        record["title"] = market["title"] or record.get("title", ticker)
        record["category"] = market["category"] or record.get("category", "unknown")
        record["last_seen"] = event["timestamp"]

        record.setdefault("events", []).append(event)

        if len(record["events"]) > MAX_EVENTS_PER_MARKET:
            record["events"] = record["events"][-MAX_EVENTS_PER_MARKET:]

        _recalculate_stats(record)
        save_memory(data)

    return {
        "ok": True,
        "ticker": ticker,
        "event_count": record["stats"]["event_count"],
        "highest_edge": record["stats"]["highest_edge"],
        "highest_score": record["stats"]["highest_score"],
    }


def remember_many(markets, source="oracle"):
    results = []
    for item in markets or []:
        results.append(remember_market(item, source=source))
    return results


def get_market_memory(ticker):
    ticker = safe_text(ticker).upper()
    with _memory_lock:
        data = load_memory()
        return data.get("markets", {}).get(ticker)


def list_markets(limit=25):
    with _memory_lock:
        data = load_memory()
        markets = list(data.get("markets", {}).values())

    markets.sort(key=lambda x: x.get("last_seen", 0), reverse=True)
    return markets[:int(limit)]


def mark_outcome(ticker, winner=None, oracle_correct=None, roi=None):
    ticker = safe_text(ticker).upper()

    with _memory_lock:
        data = load_memory()
        record = data.get("markets", {}).get(ticker)

        if not record:
            return {
                "ok": False,
                "error": "ticker_not_found",
                "ticker": ticker,
            }

        record["outcome"] = {
            "resolved": True,
            "winner": winner,
            "oracle_correct": oracle_correct,
            "roi": roi,
            "resolved_at": _now(),
        }

        save_memory(data)

    return {
        "ok": True,
        "ticker": ticker,
        "outcome": record["outcome"],
    }


def memory_summary():
    with _memory_lock:
        data = load_memory()
        markets = data.get("markets", {})

    total_events = 0
    resolved = 0
    correct = 0

    for record in markets.values():
        total_events += len(record.get("events", []))
        outcome = record.get("outcome", {})
        if outcome.get("resolved"):
            resolved += 1
            if outcome.get("oracle_correct") is True:
                correct += 1

    win_rate = round((correct / resolved) * 100, 2) if resolved else None

    return {
        "version": data.get("version", "ORACLE-029"),
        "markets": len(markets),
        "events": total_events,
        "resolved": resolved,
        "oracle_correct": correct,
        "win_rate": win_rate,
        "updated_at": data.get("updated_at"),
    }


def format_memory_summary():
    s = memory_summary()

    win_rate = "N/A" if s["win_rate"] is None else f'{s["win_rate"]}%'

    return f"""
🧠 ORACLE MARKET MEMORY

Markets Remembered:
{s["markets"]}

Total Events:
{s["events"]}

Resolved Markets:
{s["resolved"]}

Oracle Correct:
{s["oracle_correct"]}

Win Rate:
{win_rate}

Status:
Market Memory Engine active.
""".strip()


def format_market_memory(ticker):
    record = get_market_memory(ticker)

    if not record:
        return f"No memory found for {ticker}."

    stats = record.get("stats", {})
    outcome = record.get("outcome", {})
    events = record.get("events", [])

    last = events[-1] if events else {}

    return f"""
🧠 ORACLE MARKET MEMORY

Ticker:
{record.get("ticker")}

Title:
{record.get("title")}

Category:
{record.get("category")}

Events:
{stats.get("event_count", 0)}

Highest Edge:
{stats.get("highest_edge", 0)}

Average Edge:
{stats.get("average_edge", 0)}

Average Confidence:
{stats.get("average_confidence", 0)}

Highest Score:
{stats.get("highest_score", 0)}

Last Grade:
{stats.get("last_grade", "NA")}

Last Risk:
{stats.get("last_risk", "NA")}

Last Side:
{last.get("side", "NA")}

Resolved:
{outcome.get("resolved", False)}

Winner:
{outcome.get("winner")}

Oracle Correct:
{outcome.get("oracle_correct")}
""".strip()


def diagnostics():
    sample = {
        "ticker": "TEST-MEMORY",
        "title": "Test Memory Market",
        "category": "test",
        "side": "YES",
        "edge": 6.2,
        "confidence": 88,
        "fair_value": 0.63,
        "market_price": 0.57,
        "overall_score": 91,
        "grade": "A",
        "risk": "LOW",
        "reason": "Test memory event",
    }

    result = remember_market(sample, source="diagnostics")

    return {
        "module": "oracle_market_memory",
        "status": "ok" if result.get("ok") else "error",
        "result": result,
        "summary": memory_summary(),
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_memory_summary())
    print()
    print(format_market_memory("TEST-MEMORY"))
'''.lstrip(), encoding="utf-8")

print("✅ Created oracle_market_memory.py")
print("[DONE] ORACLE-029 Market Memory Engine installed")
print("")
print("Test it with:")
print("python oracle_market_memory.py")