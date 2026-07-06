from pathlib import Path

TARGET = Path("oracle_event_detection.py")

TARGET.write_text(r'''
"""
ORACLE-034 — Event Detection Engine

Purpose:
- Detect meaningful changes in Oracle opportunities
- Compare current market scorecards against previous snapshots
- Emit events only when something important changes
- Safe module: does not execute trades
"""

import json
import time
import threading
from pathlib import Path
from math import isfinite

EVENT_STATE_FILE = Path("oracle_event_state.json")
EVENT_HISTORY_FILE = Path("oracle_event_history.json")

_state_lock = threading.Lock()

DEFAULT_THRESHOLDS = {
    "edge_change": 3.0,
    "confidence_change": 10.0,
    "score_change": 8.0,
    "liquidity_change_pct": 50.0,
    "new_actionable_score": 85.0,
}


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


def load_json(path, default):
    if not path.exists():
        return default

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def normalize_card(card):
    card = card or {}

    ticker = (
        card.get("ticker")
        or card.get("market_ticker")
        or card.get("id")
        or "UNKNOWN"
    )

    title = (
        card.get("title")
        or card.get("market_title")
        or card.get("name")
        or ticker
    )

    raw = card.get("raw") if isinstance(card.get("raw"), dict) else card

    return {
        "ticker": safe_text(ticker).upper(),
        "title": safe_text(title),
        "side": safe_text(card.get("side") or raw.get("side") or "WATCH").upper(),
        "grade": safe_text(card.get("grade") or raw.get("grade") or "NA"),
        "risk": safe_text(card.get("risk") or raw.get("risk") or "NA"),
        "edge": safe_float(card.get("edge") or raw.get("edge") or raw.get("edge_score")),
        "confidence": safe_float(card.get("confidence") or raw.get("confidence") or raw.get("confidence_score")),
        "overall_score": safe_float(card.get("overall_score") or raw.get("overall_score") or raw.get("score")),
        "adaptive_score": safe_float(card.get("adaptive_score") or card.get("overall_score") or raw.get("adaptive_score")),
        "liquidity": safe_float(card.get("volume") or card.get("liquidity") or raw.get("volume") or raw.get("liquidity")),
        "fair_value": safe_float(card.get("fair_value") or raw.get("fair_value") or raw.get("oracle_fair_value")),
        "market_price": safe_float(card.get("market_price") or raw.get("market_price") or raw.get("price") or raw.get("yes_price")),
        "reason": safe_text(card.get("reason") or raw.get("reason")),
        "timestamp": now(),
    }


def percent_change(old, new):
    old = safe_float(old)
    new = safe_float(new)

    if old == 0:
        return 0.0 if new == 0 else 100.0

    return round(((new - old) / abs(old)) * 100, 2)


def priority_for_event(event_type, delta):
    delta = abs(safe_float(delta))

    if event_type in ("NEW_ACTIONABLE", "SIDE_CHANGED", "GRADE_UPGRADE"):
        return "HIGH"

    if delta >= 15:
        return "HIGH"

    if delta >= 8:
        return "MEDIUM"

    return "LOW"


def make_event(ticker, title, event_type, field, old, new, message):
    delta = safe_float(new) - safe_float(old)

    return {
        "timestamp": now(),
        "ticker": ticker,
        "title": title,
        "event_type": event_type,
        "field": field,
        "old": old,
        "new": new,
        "delta": round(delta, 4),
        "priority": priority_for_event(event_type, delta),
        "message": message,
    }


def detect_card_events(previous, current, thresholds=None):
    thresholds = thresholds or DEFAULT_THRESHOLDS
    events = []

    ticker = current["ticker"]
    title = current["title"]

    if not previous:
        if current["adaptive_score"] >= thresholds["new_actionable_score"]:
            events.append(make_event(
                ticker,
                title,
                "NEW_ACTIONABLE",
                "adaptive_score",
                0,
                current["adaptive_score"],
                "New actionable Oracle opportunity detected.",
            ))
        return events

    edge_delta = current["edge"] - previous.get("edge", 0)
    if abs(edge_delta) >= thresholds["edge_change"]:
        events.append(make_event(
            ticker,
            title,
            "EDGE_CHANGE",
            "edge",
            previous.get("edge", 0),
            current["edge"],
            "Oracle edge changed meaningfully.",
        ))

    conf_delta = current["confidence"] - previous.get("confidence", 0)
    if abs(conf_delta) >= thresholds["confidence_change"]:
        events.append(make_event(
            ticker,
            title,
            "CONFIDENCE_CHANGE",
            "confidence",
            previous.get("confidence", 0),
            current["confidence"],
            "Oracle confidence changed meaningfully.",
        ))

    score_delta = current["adaptive_score"] - previous.get("adaptive_score", 0)
    if abs(score_delta) >= thresholds["score_change"]:
        events.append(make_event(
            ticker,
            title,
            "ADAPTIVE_SCORE_CHANGE",
            "adaptive_score",
            previous.get("adaptive_score", 0),
            current["adaptive_score"],
            "Adaptive score changed meaningfully.",
        ))

    liquidity_pct = percent_change(previous.get("liquidity", 0), current["liquidity"])
    if abs(liquidity_pct) >= thresholds["liquidity_change_pct"]:
        events.append({
            "timestamp": now(),
            "ticker": ticker,
            "title": title,
            "event_type": "LIQUIDITY_CHANGE",
            "field": "liquidity",
            "old": previous.get("liquidity", 0),
            "new": current["liquidity"],
            "delta_pct": liquidity_pct,
            "priority": priority_for_event("LIQUIDITY_CHANGE", liquidity_pct),
            "message": "Liquidity changed meaningfully.",
        })

    if previous.get("side") != current["side"]:
        events.append(make_event(
            ticker,
            title,
            "SIDE_CHANGED",
            "side",
            previous.get("side"),
            current["side"],
            "Oracle recommendation side changed.",
        ))

    if previous.get("grade") != current["grade"]:
        old_grade = previous.get("grade", "NA")
        new_grade = current["grade"]

        event_type = "GRADE_CHANGE"
        if new_grade in ("A+", "A", "A-") and old_grade not in ("A+", "A", "A-"):
            event_type = "GRADE_UPGRADE"

        events.append(make_event(
            ticker,
            title,
            event_type,
            "grade",
            old_grade,
            new_grade,
            "Oracle grade changed.",
        ))

    if previous.get("adaptive_score", 0) < thresholds["new_actionable_score"] <= current["adaptive_score"]:
        events.append(make_event(
            ticker,
            title,
            "BECAME_ACTIONABLE",
            "adaptive_score",
            previous.get("adaptive_score", 0),
            current["adaptive_score"],
            "Market crossed into actionable Oracle range.",
        ))

    return events


def save_events(events):
    if not events:
        return

    history = load_json(EVENT_HISTORY_FILE, [])
    history.extend(events)
    history = history[-1000:]
    save_json(EVENT_HISTORY_FILE, history)


def process_scorecards(scorecards, thresholds=None):
    """
    Main entry point.
    Pass ranked/intelligence scorecards here.
    Returns detected events.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    detected = []

    with _state_lock:
        state = load_json(EVENT_STATE_FILE, {
            "version": "ORACLE-034",
            "updated_at": now(),
            "markets": {},
        })

        markets = state.setdefault("markets", {})

        for card in scorecards or []:
            current = normalize_card(card)

            ticker = current["ticker"]
            if ticker == "UNKNOWN":
                continue

            previous = markets.get(ticker)
            events = detect_card_events(previous, current, thresholds=thresholds)

            detected.extend(events)
            markets[ticker] = current

        state["updated_at"] = now()
        save_json(EVENT_STATE_FILE, state)
        save_events(detected)

    return detected


def get_recent_events(limit=20, priority=None):
    history = load_json(EVENT_HISTORY_FILE, [])

    if priority:
        priority = str(priority).upper()
        history = [e for e in history if e.get("priority") == priority]

    history.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
    return history[:int(limit)]


def format_event(event):
    return f"""
🔔 ORACLE EVENT

Priority:
{event.get("priority")}

Type:
{event.get("event_type")}

Ticker:
{event.get("ticker")}

Title:
{event.get("title")}

Field:
{event.get("field")}

Old:
{event.get("old")}

New:
{event.get("new")}

Message:
{event.get("message")}
""".strip()


def format_events(events):
    if not events:
        return "No Oracle events detected."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(format_event(e) for e in events)


def diagnostics():
    sample_1 = [{
        "ticker": "TEST-EVENT",
        "title": "Event Detection Test",
        "side": "YES",
        "grade": "B",
        "edge": 3.0,
        "confidence": 70,
        "adaptive_score": 76,
        "liquidity": 1000,
    }]

    sample_2 = [{
        "ticker": "TEST-EVENT",
        "title": "Event Detection Test",
        "side": "YES",
        "grade": "A",
        "edge": 8.5,
        "confidence": 91,
        "adaptive_score": 92,
        "liquidity": 3500,
    }]

    process_scorecards(sample_1)
    events = process_scorecards(sample_2)

    return {
        "module": "oracle_event_detection",
        "status": "ok",
        "events_detected": len(events),
        "recent_events": len(get_recent_events(limit=10)),
    }


if __name__ == "__main__":
    print(diagnostics())
    print()
    print(format_events(get_recent_events(limit=5)))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-034 INSTALLED")
print(" Event Detection Engine")
print("===================================")
print()
print("Created:")
print(" oracle_event_detection.py")
print()
print("Test:")
print(" python oracle_event_detection.py")