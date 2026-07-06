from pathlib import Path

TARGET = Path("oracle_similar_markets.py")

TARGET.write_text(r'''
"""
ORACLE-042 — Historical Similar Market Engine

Purpose:
- Compare live Oracle opportunities against historical Market Memory
- Find similar past setups by category, side, grade, risk, edge, confidence, and score
- Produce similarity score, historical win rate, average ROI, and confidence boost
- Safe module: no trades, no orders
"""

import json
import time
from math import isfinite

from oracle_market_memory import load_memory

try:
    from oracle_evidence_fusion import get_top_fused, fuse_cards
except Exception:
    get_top_fused = None
    fuse_cards = None


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


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, safe_float(value)))


def get_classification(item):
    cls = item.get("classification") or {}

    if not cls and isinstance(item.get("raw"), dict):
        cls = item["raw"].get("classification") or {}

    if not cls and isinstance(item.get("raw_market"), dict):
        cls = {
            "domain": item["raw_market"].get("category", "unknown"),
            "subtype": "general",
            "category": item["raw_market"].get("category", "unknown"),
        }

    if not isinstance(cls, dict):
        cls = {}

    return {
        "domain": str(cls.get("domain") or item.get("category") or "unknown").lower(),
        "subtype": str(cls.get("subtype") or "general").lower(),
        "category": str(cls.get("category") or item.get("category") or "unknown").lower(),
    }


def latest_event(record):
    events = record.get("events", [])
    return events[-1] if events else {}


def normalize_live_card(card):
    cls = get_classification(card)

    return {
        "ticker": card.get("ticker", "UNKNOWN"),
        "title": card.get("title", ""),
        "domain": cls["domain"],
        "subtype": cls["subtype"],
        "category": cls["category"],
        "side": str(card.get("side") or card.get("recommendation") or card.get("fused_recommendation") or "WATCH").upper(),
        "grade": str(card.get("fused_grade") or card.get("grade") or "NA").upper(),
        "risk": str(card.get("risk") or "NA").upper(),
        "edge": safe_float(card.get("edge")),
        "confidence": safe_float(card.get("confidence")),
        "score": safe_float(card.get("evidence_score") or card.get("opportunity_score") or card.get("overall_score")),
        "recommendation": str(card.get("fused_recommendation") or card.get("recommendation") or "PASS").upper(),
        "raw": card,
    }


def normalize_memory_record(record):
    last = latest_event(record)
    cls = get_classification(record)

    return {
        "ticker": record.get("ticker", "UNKNOWN"),
        "title": record.get("title", ""),
        "domain": cls["domain"],
        "subtype": cls["subtype"],
        "category": cls["category"],
        "side": str(last.get("side") or "WATCH").upper(),
        "grade": str(last.get("grade") or "NA").upper(),
        "risk": str(last.get("risk") or "NA").upper(),
        "edge": safe_float(last.get("edge")),
        "confidence": safe_float(last.get("confidence")),
        "score": safe_float(last.get("overall_score")),
        "outcome": record.get("outcome", {}),
        "raw": record,
    }


def distance_score(live, hist):
    score = 0.0

    if live["domain"] == hist["domain"]:
        score += 25
    if live["subtype"] == hist["subtype"]:
        score += 10
    if live["category"] == hist["category"]:
        score += 10
    if live["side"] == hist["side"]:
        score += 10
    if live["grade"] == hist["grade"]:
        score += 8
    if live["risk"] == hist["risk"]:
        score += 7

    edge_diff = abs(live["edge"] - hist["edge"])
    conf_diff = abs(live["confidence"] - hist["confidence"])
    score_diff = abs(live["score"] - hist["score"])

    score += max(0, 15 - edge_diff * 150)
    score += max(0, 10 - conf_diff * 0.5)
    score += max(0, 5 - score_diff * 0.15)

    return round(clamp(score), 2)


def find_similar_markets(card, limit=10, min_similarity=35):
    live = normalize_live_card(card)
    db = load_memory()
    markets = db.get("markets", {})

    matches = []

    for record in markets.values():
        hist = normalize_memory_record(record)

        if hist["ticker"] == live["ticker"]:
            continue

        sim = distance_score(live, hist)

        if sim < min_similarity:
            continue

        outcome = hist.get("outcome", {})

        matches.append({
            "ticker": hist["ticker"],
            "title": hist["title"],
            "similarity": sim,
            "side": hist["side"],
            "grade": hist["grade"],
            "risk": hist["risk"],
            "edge": hist["edge"],
            "confidence": hist["confidence"],
            "score": hist["score"],
            "resolved": outcome.get("resolved", False),
            "oracle_correct": outcome.get("oracle_correct"),
            "roi": outcome.get("roi"),
        })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:int(limit)]


def summarize_matches(matches):
    resolved = [m for m in matches if m.get("resolved")]
    wins = [m for m in resolved if m.get("oracle_correct") is True]
    rois = [safe_float(m.get("roi")) for m in resolved if m.get("roi") is not None]

    win_rate = round(len(wins) / len(resolved) * 100, 2) if resolved else None
    avg_roi = round(sum(rois) / len(rois), 2) if rois else None

    confidence_boost = 0.0
    if resolved and win_rate is not None:
        if win_rate >= 75:
            confidence_boost = 10.0
        elif win_rate >= 65:
            confidence_boost = 6.0
        elif win_rate >= 55:
            confidence_boost = 3.0
        elif win_rate < 45:
            confidence_boost = -6.0

    return {
        "matches": len(matches),
        "resolved": len(resolved),
        "wins": len(wins),
        "win_rate": win_rate,
        "avg_roi": avg_roi,
        "confidence_boost": confidence_boost,
    }


def analyze_card_similarity(card, limit=10):
    matches = find_similar_markets(card, limit=limit)
    summary = summarize_matches(matches)

    output = dict(card)
    output["similar_markets"] = matches
    output["similarity_summary"] = summary
    output["similarity_score"] = round(
        (sum(m["similarity"] for m in matches) / len(matches)) if matches else 0,
        2,
    )

    return output


def analyze_top_cards(limit=10):
    cards = []

    if fuse_cards:
        try:
            fuse_cards(limit=50)
        except Exception:
            pass

    if get_top_fused:
        try:
            cards = get_top_fused(limit=limit)
        except Exception:
            cards = []

    return [analyze_card_similarity(card, limit=10) for card in cards]


def format_similarity_report(card):
    summary = card.get("similarity_summary", {})
    matches = card.get("similar_markets", [])[:5]

    win_rate = summary.get("win_rate")
    avg_roi = summary.get("avg_roi")

    win_rate_text = "N/A" if win_rate is None else f"{win_rate}%"
    avg_roi_text = "N/A" if avg_roi is None else f"{avg_roi}%"

    lines = []
    lines.append("🧠 ORACLE SIMILAR MARKET ANALYSIS")
    lines.append("")
    lines.append(f"Ticker:\n{card.get('ticker')}")
    lines.append("")
    lines.append(f"Title:\n{card.get('title')}")
    lines.append("")
    lines.append(f"Recommendation:\n{card.get('fused_recommendation') or card.get('recommendation')}")
    lines.append("")
    lines.append(f"Similar Matches:\n{summary.get('matches', 0)}")
    lines.append(f"Resolved Matches:\n{summary.get('resolved', 0)}")
    lines.append(f"Historical Win Rate:\n{win_rate_text}")
    lines.append(f"Average ROI:\n{avg_roi_text}")
    lines.append(f"Confidence Boost:\n{summary.get('confidence_boost', 0)}")
    lines.append("")

    if matches:
        lines.append("Closest Historical Matches:")
        for m in matches:
            lines.append(
                f"• {m.get('ticker')} | similarity {m.get('similarity')} | "
                f"correct={m.get('oracle_correct')} | roi={m.get('roi')}"
            )
    else:
        lines.append("Closest Historical Matches:\nNone yet. Oracle needs more resolved history.")

    return "\n".join(lines)


def format_top_similarity(limit=5):
    cards = analyze_top_cards(limit=limit)

    if not cards:
        return "No similar-market analysis available."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_similarity_report(card)
        for card in cards
    )


def diagnostics():
    cards = analyze_top_cards(limit=5)

    return {
        "module": "oracle_similar_markets",
        "status": "ok",
        "cards_analyzed": len(cards),
        "top": [
            {
                "ticker": c.get("ticker"),
                "matches": c.get("similarity_summary", {}).get("matches"),
                "resolved": c.get("similarity_summary", {}).get("resolved"),
                "win_rate": c.get("similarity_summary", {}).get("win_rate"),
                "confidence_boost": c.get("similarity_summary", {}).get("confidence_boost"),
            }
            for c in cards
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top_similarity(limit=3))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-042 INSTALLED")
print(" Historical Similar Market Engine")
print("===================================")
print()
print("Created:")
print(" oracle_similar_markets.py")
print()
print("Test:")
print(" python oracle_similar_markets.py")