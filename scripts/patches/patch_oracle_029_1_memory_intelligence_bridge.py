from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        backup_path = path.with_suffix(path.suffix + f".bak_{stamp}")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup created: {backup_path.name}")

target = ROOT / "oracle_memory_bridge.py"
backup(target)

target.write_text(r'''
"""
ORACLE-029.1 — Memory Intelligence Bridge

Purpose:
- Connect ORACLE-028 Opportunity Intelligence to ORACLE-029 Market Memory
- Analyze opportunities into scorecards
- Save scorecards into Oracle memory
- Return ranked intelligence cards for feeds, dashboards, and future learning
- Safe module: does not execute trades
"""

from oracle_opportunity_intelligence import analyze_opportunity, analyze_opportunities
from oracle_market_memory import remember_market, remember_many, memory_summary


def score_and_remember_opportunity(opportunity, source="oracle_intelligence"):
    """
    Analyze one opportunity, save it to market memory, and return the scorecard.
    """
    card = analyze_opportunity(opportunity)

    try:
        remember_market(card, source=source)
    except Exception as e:
        card["memory_error"] = str(e)

    return card


def score_and_remember_many(opportunities, source="oracle_intelligence", min_grade=None, limit=None):
    """
    Analyze many opportunities, rank them, save them to market memory, and return scorecards.
    """
    cards = analyze_opportunities(
        opportunities or [],
        min_grade=min_grade,
        limit=limit,
    )

    for card in cards:
        try:
            remember_market(card, source=source)
        except Exception as e:
            card["memory_error"] = str(e)

    return cards


def remember_existing_scorecards(scorecards, source="oracle_scorecard"):
    """
    Save already-created scorecards into market memory.
    """
    results = []

    for card in scorecards or []:
        try:
            results.append(remember_market(card, source=source))
        except Exception as e:
            results.append({
                "ok": False,
                "error": str(e),
                "ticker": card.get("ticker", "UNKNOWN") if isinstance(card, dict) else "UNKNOWN",
            })

    return results


def bridge_diagnostics():
    sample = [
        {
            "ticker": "TEST-BRIDGE-YES",
            "title": "Bridge Test Market YES",
            "side": "YES",
            "edge": 7.8,
            "confidence": 91,
            "fair_value": 0.66,
            "market_price": 0.58,
            "volume": 35000,
            "age_seconds": 40,
            "providers": ["oracle", "cache", "research"],
        },
        {
            "ticker": "TEST-BRIDGE-NO",
            "title": "Bridge Test Market NO",
            "side": "NO",
            "edge": 4.4,
            "confidence": 73,
            "fair_value": 0.41,
            "market_price": 0.46,
            "volume": 1800,
            "age_seconds": 220,
            "providers": ["oracle"],
        },
    ]

    cards = score_and_remember_many(sample, source="bridge_diagnostics")

    return {
        "module": "oracle_memory_bridge",
        "status": "ok",
        "cards_created": len(cards),
        "top_ticker": cards[0]["ticker"] if cards else None,
        "top_grade": cards[0]["grade"] if cards else None,
        "memory": memory_summary(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(bridge_diagnostics(), indent=2))
'''.lstrip(), encoding="utf-8")

print("✅ Created oracle_memory_bridge.py")
print("[DONE] ORACLE-029.1 Memory Intelligence Bridge installed")
print("")
print("Test it with:")
print("python oracle_memory_bridge.py")