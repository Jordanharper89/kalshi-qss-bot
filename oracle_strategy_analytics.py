"""
ORACLE-031 — Strategy Analytics Engine

Purpose:
- Analyze Oracle historical performance
- Break down results by grade
- Break down results by recommendation side
- Measure ROI
- Produce strategy statistics for future self-learning

Requires:
    oracle_market_memory.py
"""

from math import isfinite

from oracle_market_memory import load_memory


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if not isfinite(value):
            return default
        return value
    except Exception:
        return default


def empty_bucket():
    return {
        "markets": 0,
        "wins": 0,
        "losses": 0,
        "roi": 0.0,
    }


def analyze():
    db = load_memory()

    grades = {}
    sides = {
        "YES": empty_bucket(),
        "NO": empty_bucket(),
    }

    total = empty_bucket()

    for record in db.get("markets", {}).values():

        outcome = record.get("outcome", {})

        if not outcome.get("resolved"):
            continue

        events = record.get("events", [])

        if not events:
            continue

        last = events[-1]

        grade = last.get("grade", "UNKNOWN")
        side = last.get("side", "WATCH")

        roi = safe_float(outcome.get("roi"))

        if grade not in grades:
            grades[grade] = empty_bucket()

        grades[grade]["markets"] += 1
        grades[grade]["roi"] += roi

        total["markets"] += 1
        total["roi"] += roi

        if outcome.get("oracle_correct"):
            grades[grade]["wins"] += 1
            total["wins"] += 1
        else:
            grades[grade]["losses"] += 1
            total["losses"] += 1

        if side in sides:
            sides[side]["markets"] += 1
            sides[side]["roi"] += roi

            if outcome.get("oracle_correct"):
                sides[side]["wins"] += 1
            else:
                sides[side]["losses"] += 1

    return {
        "grades": grades,
        "sides": sides,
        "overall": total,
    }


def _pct(wins, total):
    if total == 0:
        return 0.0
    return round((wins / total) * 100, 2)


def report():
    data = analyze()

    out = []

    out.append("🧠 ORACLE STRATEGY ANALYTICS")
    out.append("")

    overall = data["overall"]

    out.append("OVERALL")
    out.append(f"Markets : {overall['markets']}")
    out.append(f"Wins    : {overall['wins']}")
    out.append(f"Losses  : {overall['losses']}")
    out.append(f"Win %   : {_pct(overall['wins'], overall['markets'])}%")
    out.append(f"ROI     : {round(overall['roi'],2)}%")
    out.append("")

    out.append("BY GRADE")

    for grade in sorted(data["grades"]):
        g = data["grades"][grade]

        out.append(
            f"{grade:>3} | "
            f"{g['markets']:4} | "
            f"{_pct(g['wins'], g['markets']):6}% | "
            f"{round(g['roi'],2):8}%"
        )

    out.append("")
    out.append("BY SIDE")

    for side in ("YES", "NO"):
        s = data["sides"][side]

        out.append(
            f"{side:>3} | "
            f"{s['markets']:4} | "
            f"{_pct(s['wins'], s['markets']):6}% | "
            f"{round(s['roi'],2):8}%"
        )

    return "\n".join(out)


def diagnostics():
    data = analyze()

    return {
        "module": "oracle_strategy_analytics",
        "status": "ok",
        "markets": data["overall"]["markets"],
    }


if __name__ == "__main__":
    print(report())
