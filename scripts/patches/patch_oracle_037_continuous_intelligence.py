from pathlib import Path

TARGET = Path("oracle_continuous_intelligence.py")

TARGET.write_text(r'''
"""
ORACLE-037 — Continuous Intelligence Pipeline

Purpose:
- Run Oracle intelligence cycles in the background
- Pull opportunities from available Oracle sources
- Rank opportunities through ORACLE-033
- Save memory through ORACLE-029
- Detect events through ORACLE-034
- Maintain a live pipeline status snapshot

Safe module:
- Does not execute trades
- Does not place orders
"""

import time
import threading
import traceback

from oracle_event_pipeline import process_opportunities


DEFAULT_INTERVAL_SECONDS = 10.0

_lock = threading.Lock()
_thread = None
_running = False

_state = {
    "running": False,
    "started_at": None,
    "last_cycle_at": None,
    "last_error": None,
    "cycles_completed": 0,
    "opportunities_seen": 0,
    "ranked_count": 0,
    "events_detected": 0,
    "high_priority_events": 0,
    "last_ranked": [],
    "last_events": [],
}


def _now():
    return time.time()


def _safe_import_opportunities():
    """
    Best-effort opportunity loading.

    Tries current Oracle modules without requiring one exact interface.
    Returns a list.
    """
    # 1) Existing opportunity feed builder
    try:
        from oracle_opportunity_feed import build_oracle_opportunity_feed

        try:
            opportunities = build_oracle_opportunity_feed(
                watched_markets=[],
                min_grade="C",
                min_edge=0,
                min_confidence=0,
                max_items=50,
            )
        except TypeError:
            opportunities = build_oracle_opportunity_feed()

        if isinstance(opportunities, list):
            return opportunities

    except Exception:
        pass

    # 2) Research engine snapshot
    try:
        from oracle_research_engine import oracle_research_engine

        snap = oracle_research_engine.get_snapshot()

        if isinstance(snap, dict):
            for key in ("opportunities", "ranked", "signals", "markets"):
                value = snap.get(key)
                if isinstance(value, list):
                    return value

    except Exception:
        pass

    # 3) Market cache diagnostics only fallback: no opportunities
    return []


def run_cycle(opportunities=None):
    """
    Run one complete intelligence cycle.
    Can be called manually for testing.
    """
    global _state

    started = _now()

    try:
        if opportunities is None:
            opportunities = _safe_import_opportunities()

        opportunities = opportunities or []

        result = process_opportunities(
            opportunities,
            limit=25,
            remember=True,
            detect_events=True,
        )

        ranked = result.get("ranked", [])
        events = result.get("events", [])
        high_events = [e for e in events if str(e.get("priority", "")).upper() == "HIGH"]

        with _lock:
            _state["running"] = _running
            _state["last_cycle_at"] = started
            _state["last_error"] = None
            _state["cycles_completed"] += 1
            _state["opportunities_seen"] = len(opportunities)
            _state["ranked_count"] = len(ranked)
            _state["events_detected"] = len(events)
            _state["high_priority_events"] = len(high_events)
            _state["last_ranked"] = ranked[:10]
            _state["last_events"] = events[:10]

        return {
            "ok": True,
            "opportunities_seen": len(opportunities),
            "ranked": len(ranked),
            "events": len(events),
            "high_priority_events": len(high_events),
        }

    except Exception as e:
        err = traceback.format_exc()

        with _lock:
            _state["last_cycle_at"] = started
            _state["last_error"] = str(e)

        print("[ORACLE-037] Continuous intelligence cycle error:")
        print(err)

        return {
            "ok": False,
            "error": str(e),
        }


def _loop(interval_seconds):
    global _running

    while _running:
        run_cycle()
        time.sleep(interval_seconds)


def start(interval_seconds=DEFAULT_INTERVAL_SECONDS):
    """
    Start the continuous intelligence pipeline.
    Safe to call multiple times.
    """
    global _thread, _running, _state

    if _running:
        return {
            "ok": True,
            "already_running": True,
        }

    _running = True

    with _lock:
        _state["running"] = True
        _state["started_at"] = _now()
        _state["last_error"] = None

    _thread = threading.Thread(
        target=_loop,
        args=(float(interval_seconds),),
        daemon=True,
        name="OracleContinuousIntelligence",
    )
    _thread.start()

    print(f"[ORACLE-037] Continuous Intelligence Pipeline started interval={interval_seconds}s")

    return {
        "ok": True,
        "started": True,
        "interval_seconds": float(interval_seconds),
    }


def stop():
    global _running

    _running = False

    with _lock:
        _state["running"] = False

    print("[ORACLE-037] Continuous Intelligence Pipeline stopped")

    return {
        "ok": True,
        "stopped": True,
    }


def status():
    with _lock:
        snap = dict(_state)

    if snap.get("last_cycle_at"):
        snap["age_seconds"] = round(_now() - snap["last_cycle_at"], 2)
    else:
        snap["age_seconds"] = None

    return snap


def format_status():
    s = status()

    return f"""
🧠 ORACLE CONTINUOUS INTELLIGENCE

Running:
{s.get("running")}

Cycles Completed:
{s.get("cycles_completed")}

Last Cycle Age:
{s.get("age_seconds")}

Opportunities Seen:
{s.get("opportunities_seen")}

Ranked:
{s.get("ranked_count")}

Events Detected:
{s.get("events_detected")}

High Priority Events:
{s.get("high_priority_events")}

Last Error:
{s.get("last_error")}

Status:
Continuous Intelligence Pipeline installed.
""".strip()


def diagnostics():
    result = run_cycle(opportunities=[
        {
            "ticker": "TEST-CONTINUOUS-1",
            "title": "Continuous Intelligence Test",
            "side": "YES",
            "edge": 8.6,
            "confidence": 92,
            "fair_value": 0.69,
            "market_price": 0.59,
            "volume": 42000,
            "age_seconds": 35,
            "providers": ["oracle", "cache", "research"],
        }
    ])

    return {
        "module": "oracle_continuous_intelligence",
        "status": "ok",
        "cycle_result": result,
        "pipeline_status": status(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_status())
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-037 INSTALLED")
print(" Continuous Intelligence Pipeline")
print("===================================")
print()
print("Created:")
print(" oracle_continuous_intelligence.py")
print()
print("Test:")
print(" python oracle_continuous_intelligence.py")