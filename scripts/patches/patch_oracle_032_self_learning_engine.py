from pathlib import Path

TARGET = Path("oracle_self_learning.py")

TARGET.write_text(r'''
"""
====================================================
ORACLE-032 SELF LEARNING ENGINE
====================================================

Purpose

Learn from Oracle's historical decisions.

This engine does NOT use AI.

It statistically learns which combinations of:

• Grade
• Side
• Edge
• Confidence

have historically produced the highest win rate.

Future Oracle rankings can then boost opportunities
that resemble historically successful trades.

====================================================
"""

from math import isfinite

from oracle_market_memory import load_memory


EDGE_BUCKETS = [
    (0,2),
    (2,4),
    (4,6),
    (6,8),
    (8,10),
    (10,999),
]

CONF_BUCKETS = [
    (0,60),
    (60,70),
    (70,80),
    (80,90),
    (90,101),
]


def safe_float(x, default=0):
    try:
        x=float(x)
        if not isfinite(x):
            return default
        return x
    except:
        return default


def bucket(value, buckets):

    for low,high in buckets:
        if low <= value < high:
            return f"{low}-{high}"

    return "Unknown"


def empty():

    return {
        "markets":0,
        "wins":0,
        "losses":0,
        "roi":0.0
    }


def analyze():

    db=load_memory()

    grade_stats={}
    edge_stats={}
    conf_stats={}
    combo_stats={}

    for record in db["markets"].values():

        outcome=record.get("outcome",{})

        if not outcome.get("resolved"):
            continue

        if not record["events"]:
            continue

        last=record["events"][-1]

        grade=last.get("grade","?")
        edge=safe_float(last.get("edge"))
        conf=safe_float(last.get("confidence"))

        edge_bucket=bucket(edge,EDGE_BUCKETS)
        conf_bucket=bucket(conf,CONF_BUCKETS)

        combo=f"{grade}|{edge_bucket}|{conf_bucket}"

        for table,key in (
            (grade_stats,grade),
            (edge_stats,edge_bucket),
            (conf_stats,conf_bucket),
            (combo_stats,combo),
        ):

            if key not in table:
                table[key]=empty()

            table[key]["markets"]+=1
            table[key]["roi"]+=safe_float(outcome.get("roi"))

            if outcome.get("oracle_correct"):
                table[key]["wins"]+=1
            else:
                table[key]["losses"]+=1

    return {
        "grade":grade_stats,
        "edge":edge_stats,
        "confidence":conf_stats,
        "combo":combo_stats,
    }


def winrate(bucket):

    total=bucket["markets"]

    if total==0:
        return 0

    return round(bucket["wins"]/total*100,2)


def rank_patterns():

    data=analyze()

    ranked=[]

    for combo,stats in data["combo"].items():

        ranked.append({
            "pattern":combo,
            "markets":stats["markets"],
            "winrate":winrate(stats),
            "roi":round(stats["roi"],2),
        })

    ranked.sort(
        key=lambda x:(x["winrate"],x["roi"],x["markets"]),
        reverse=True
    )

    return ranked


def report():

    ranked=rank_patterns()

    out=[]

    out.append("🧠 ORACLE SELF LEARNING")
    out.append("")

    out.append("TOP HISTORICAL PATTERNS")
    out.append("")

    for item in ranked[:20]:

        out.append(
            f"{item['pattern']}"
        )

        out.append(
            f" Markets : {item['markets']}"
        )

        out.append(
            f" WinRate : {item['winrate']}%"
        )

        out.append(
            f" ROI : {item['roi']}%"
        )

        out.append("")

    return "\n".join(out)


def recommend_multiplier(
    grade,
    edge,
    confidence,
):

    combo=f"{grade}|{bucket(edge,EDGE_BUCKETS)}|{bucket(confidence,CONF_BUCKETS)}"

    for item in rank_patterns():

        if item["pattern"]==combo:

            if item["markets"]<10:
                return 1.00

            if item["winrate"]>=80:
                return 1.25

            if item["winrate"]>=70:
                return 1.15

            if item["winrate"]>=60:
                return 1.05

            if item["winrate"]<45:
                return 0.85

            return 1.00

    return 1.00


def diagnostics():

    ranked=rank_patterns()

    return {

        "module":"oracle_self_learning",

        "patterns":len(ranked),

        "status":"ok",
    }


if __name__=="__main__":

    print(report())

    print()

    print(diagnostics())
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-032 INSTALLED")
print(" Self Learning Engine")
print("===================================")
print()
print("Created:")
print(" oracle_self_learning.py")
print()
print("Test:")
print(" python oracle_self_learning.py")