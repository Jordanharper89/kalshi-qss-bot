from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
TARGET = ROOT / "oracle_outcome_tracker.py"

TARGET.write_text(r'''
"""
ORACLE-030 — Outcome Tracker

Purpose:
- Resolve finished prediction markets
- Record Oracle correctness
- Record realized ROI
- Feed Market Memory for future learning
"""

import time
from math import isfinite

from oracle_market_memory import (
    mark_outcome,
    get_market_memory,
    memory_summary,
)


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if not isfinite(value):
            return default
        return value
    except Exception:
        return default


def determine_correct(last_side, winner):
    last_side = str(last_side or "").upper()
    winner = str(winner or "").upper()

    if winner not in ("YES", "NO"):
        return None

    return last_side == winner


def resolve_market(
    ticker,
    winner,
    settlement_price=1.0,
):
    """
    winner:
        YES / NO
    settlement_price:
        1.0 for winner
        0.0 for loser
    """

    record = get_market_memory(ticker)

    if not record:
        return {
            "ok": False,
            "error": "unknown_market",
            "ticker": ticker,
        }

    events = record.get("events", [])

    if not events:
        return {
            "ok": False,
            "error": "no_events",
            "ticker": ticker,
        }

    last = events[-1]

    side = last.get("side", "WATCH")

    oracle_correct = determine_correct(side, winner)

    entry = safe_float(last.get("market_price"))

    if oracle_correct is None:
        roi = None
    else:
        if entry <= 0:
            roi = None
        elif oracle_correct:
            roi = round((settlement_price - entry) / entry * 100, 2)
        else:
            roi = -100.0

    result = mark_outcome(
        ticker=ticker,
        winner=winner,
        oracle_correct=oracle_correct,
        roi=roi,
    )

    result["side"] = side
    result["roi"] = roi

    return result


def resolve_many(results):
    output = []

    for item in results:
        output.append(
            resolve_market(
                ticker=item["ticker"],
                winner=item["winner"],
                settlement_price=item.get("settlement_price", 1.0),
            )
        )

    return output


def outcome_statistics():
    summary = memory_summary()

    return {
        "markets": summary["markets"],
        "resolved": summary["resolved"],
        "oracle_correct": summary["oracle_correct"],
        "win_rate": summary["win_rate"],
    }


def diagnostics():
    return {
        "module": "oracle_outcome_tracker",
        "status": "ok",
        "statistics": outcome_statistics(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("====================================")
print(" ORACLE-030 INSTALLED")
print(" Outcome Tracker")
print("====================================")
print()
print("Created:")
print(" oracle_outcome_tracker.py")
print()
print("Test:")
print(" python oracle_outcome_tracker.py")