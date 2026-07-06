"""
ORACLE-036 — Event Pipeline

Purpose:
- Connect adaptive ranking to event detection
- Take live/raw Oracle opportunities
- Score them with ORACLE-033 adaptive ranking
- Save intelligence to Market Memory
- Detect meaningful changes with ORACLE-034
- Return ranked cards + events

Safe module:
- Does not execute trades
- Does not place orders
"""

from oracle_adaptive_ranking import rank_opportunities, format_ranked_opportunities
from oracle_memory_bridge import remember_existing_scorecards
from oracle_event_detection import process_scorecards, format_events


def process_opportunities(opportunities, limit=10, remember=True, detect_events=True):
    ranked = rank_opportunities(opportunities or [], limit=limit)

    memory_results = []
    events = []

    if remember:
        try:
            memory_results = remember_existing_scorecards(
                ranked,
                source="oracle_event_pipeline",
            )
        except Exception as e:
            memory_results = [{
                "ok": False,
                "error": str(e),
            }]

    if detect_events:
        try:
            events = process_scorecards(ranked)
        except Exception as e:
            events = [{
                "event_type": "PIPELINE_ERROR",
                "priority": "HIGH",
                "ticker": "SYSTEM",
                "title": "Oracle Event Pipeline",
                "field": "pipeline",
                "old": "ok",
                "new": "error",
                "message": str(e),
            }]

    return {
        "ranked": ranked,
        "events": events,
        "memory_results": memory_results,
    }


def pipeline_report(opportunities, limit=10):
    result = process_opportunities(opportunities, limit=limit)

    ranked_text = format_ranked_opportunities(result["ranked"])
    events_text = format_events(result["events"])

    return f"""
🧠 ORACLE EVENT PIPELINE REPORT

RANKED OPPORTUNITIES
━━━━━━━━━━━━━━━━━━━━━━

{ranked_text}

EVENTS DETECTED
━━━━━━━━━━━━━━━━━━━━━━

{events_text}
""".strip()


def diagnostics():
    sample = [
        {
            "ticker": "TEST-PIPE-1",
            "title": "Pipeline Test Market 1",
            "side": "YES",
            "edge": 8.8,
            "confidence": 93,
            "fair_value": 0.69,
            "market_price": 0.59,
            "volume": 45000,
            "age_seconds": 35,
            "providers": ["oracle", "cache", "research"],
        },
        {
            "ticker": "TEST-PIPE-2",
            "title": "Pipeline Test Market 2",
            "side": "NO",
            "edge": 3.4,
            "confidence": 71,
            "fair_value": 0.43,
            "market_price": 0.47,
            "volume": 1200,
            "age_seconds": 180,
            "providers": ["oracle"],
        },
    ]

    result = process_opportunities(sample, limit=10)

    return {
        "module": "oracle_event_pipeline",
        "status": "ok",
        "ranked": len(result["ranked"]),
        "events": len(result["events"]),
        "memory_results": len(result["memory_results"]),
    }


if __name__ == "__main__":
    print(diagnostics())
    print()
    print(pipeline_report([
        {
            "ticker": "TEST-PIPE-1",
            "title": "Pipeline Test Market 1",
            "side": "YES",
            "edge": 8.8,
            "confidence": 93,
            "fair_value": 0.69,
            "market_price": 0.59,
            "volume": 45000,
            "age_seconds": 35,
            "providers": ["oracle", "cache", "research"],
        }
    ]))
