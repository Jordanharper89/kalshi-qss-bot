from pathlib import Path

TARGET = Path("oracle_final_fusion.py")

TARGET.write_text(r'''
"""
ORACLE-043 — Evidence + Similarity Fusion

Purpose:
- Combine Evidence Fusion with Historical Similar Market analysis
- Apply confidence boosts/penalties from similar historical setups
- Produce final Oracle score, grade, recommendation, and rank
- Safe: no trades, no orders
"""

import json
import time
from pathlib import Path
from math import isfinite

from oracle_evidence_fusion import fuse_cards, get_top_fused
from oracle_similar_markets import analyze_card_similarity

FINAL_FUSION_FILE = Path("oracle_final_fusion.json")


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


def final_recommendation(score, card):
    current = str(card.get("fused_recommendation") or "PASS").upper()
    confidence = safe_float(card.get("confidence"))
    edge = safe_float(card.get("edge"))

    if score >= 86 and confidence >= 82 and abs(edge) >= 0.06:
        return "BUY YES" if edge > 0 else "BUY NO"

    if score >= 72 and confidence >= 74 and abs(edge) >= 0.035:
        return "LEAN YES" if edge > 0 else "LEAN NO"

    if score >= 55:
        return "WATCH"

    return "PASS"


def final_grade(score, recommendation):
    rec = str(recommendation or "PASS").upper()
    score = safe_float(score)

    if rec in ("BUY YES", "BUY NO") and score >= 90:
        return "A+"
    if rec in ("BUY YES", "BUY NO") and score >= 84:
        return "A"
    if rec in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO") and score >= 76:
        return "A-"
    if score >= 68:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 52:
        return "B-"
    if score >= 42:
        return "C"
    return "PASS"


def similarity_adjustment(summary):
    if not summary:
        return 0.0

    matches = int(summary.get("matches") or 0)
    resolved = int(summary.get("resolved") or 0)
    win_rate = summary.get("win_rate")
    avg_roi = summary.get("avg_roi")
    boost = safe_float(summary.get("confidence_boost"))

    if matches == 0:
        return 0.0

    adj = boost

    if resolved < 5:
        adj *= 0.35
    elif resolved < 15:
        adj *= 0.65

    if win_rate is not None:
        win_rate = safe_float(win_rate)
        if win_rate >= 75:
            adj += 6
        elif win_rate >= 65:
            adj += 3
        elif win_rate < 45:
            adj -= 6

    if avg_roi is not None:
        avg_roi = safe_float(avg_roi)
        if avg_roi >= 8:
            adj += 4
        elif avg_roi >= 3:
            adj += 2
        elif avg_roi < -3:
            adj -= 4

    return round(adj, 2)


def fuse_final_card(card):
    sim_card = analyze_card_similarity(card, limit=10)
    summary = sim_card.get("similarity_summary", {})

    evidence_score = safe_float(card.get("evidence_score"))
    fused_rank = safe_float(card.get("fused_rank_score"))
    confidence = safe_float(card.get("confidence"))
    edge = abs(safe_float(card.get("edge")))

    sim_adj = similarity_adjustment(summary)

    final_score = clamp(
        evidence_score * 0.45
        + fused_rank * 0.25
        + confidence * 0.20
        + min(edge * 300, 20) * 0.10
        + sim_adj
    )

    rec = final_recommendation(final_score, card)
    grade = final_grade(final_score, rec)

    output = dict(sim_card)
    output["similarity_adjustment"] = sim_adj
    output["final_score"] = round(final_score, 2)
    output["final_recommendation"] = rec
    output["final_grade"] = grade
    output["final_rank_score"] = final_rank_score(output)
    output["final_thesis"] = build_final_thesis(output)
    output["final_created_at"] = now()

    return output


def final_rank_score(card):
    rec = str(card.get("final_recommendation") or "PASS").upper()
    score = safe_float(card.get("final_score"))
    sim_adj = safe_float(card.get("similarity_adjustment"))

    rank = score

    if rec in ("BUY YES", "BUY NO"):
        rank += 18
    elif rec in ("LEAN YES", "LEAN NO"):
        rank += 9
    elif rec == "PASS":
        rank -= 15

    rank += max(-10, min(10, sim_adj))

    return round(clamp(rank), 2)


def build_final_thesis(card):
    lines = []
    lines.append(f"{card.get('ticker')}: {card.get('final_recommendation')} ({card.get('final_grade')})")
    lines.append(f"Final Score: {card.get('final_score')}")
    lines.append(f"Evidence Score: {card.get('evidence_score')}")
    lines.append(f"Similarity Adjustment: {card.get('similarity_adjustment')}")
    lines.append("")

    summary = card.get("similarity_summary", {})
    if summary:
        lines.append("Historical Similarity:")
        lines.append(f"• Matches: {summary.get('matches')}")
        lines.append(f"• Resolved: {summary.get('resolved')}")
        lines.append(f"• Win Rate: {summary.get('win_rate')}")
        lines.append(f"• Avg ROI: {summary.get('avg_roi')}")
        lines.append("")

    thesis = card.get("trade_thesis")
    if thesis:
        lines.append("Evidence Thesis:")
        lines.append(thesis)

    return "\n".join(lines)


def run_final_fusion(limit=50):
    try:
        fuse_cards(limit=limit)
    except Exception:
        pass

    cards = get_top_fused(limit=limit)
    final_cards = [fuse_final_card(card) for card in cards]

    final_cards.sort(
        key=lambda x: (
            x.get("final_rank_score", 0),
            x.get("final_score", 0),
            x.get("evidence_score", 0),
        ),
        reverse=True,
    )

    payload = {
        "version": "ORACLE-043",
        "updated_at": now(),
        "count": len(final_cards),
        "cards": final_cards,
    }

    FINAL_FUSION_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_top_final(limit=10):
    if not FINAL_FUSION_FILE.exists():
        run_final_fusion(limit=max(50, limit))

    try:
        data = json.loads(FINAL_FUSION_FILE.read_text(encoding="utf-8"))
        cards = data.get("cards", [])
        return cards[:int(limit)]
    except Exception:
        return []


def format_final_card(card, rank=None):
    rank_line = f"Rank #{rank}" if rank else "Final Oracle Card"

    summary = card.get("similarity_summary", {})
    win_rate = summary.get("win_rate")
    avg_roi = summary.get("avg_roi")

    return f"""
🔮 ORACLE FINAL FUSION

{rank_line}

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Final Recommendation:
{card.get("final_recommendation")}

Final Grade:
{card.get("final_grade")}

Final Score:
{card.get("final_score")}

Final Rank Score:
{card.get("final_rank_score")}

Evidence Score:
{card.get("evidence_score")}

Similarity Adjustment:
{card.get("similarity_adjustment")}

Market Price:
{card.get("market_price")}

Fair Value:
{card.get("fair_value")}

Edge:
{round(safe_float(card.get("edge")) * 100, 2)}%

Confidence:
{card.get("confidence")}

Similar Matches:
{summary.get("matches", 0)}

Resolved Matches:
{summary.get("resolved", 0)}

Historical Win Rate:
{win_rate if win_rate is not None else "N/A"}

Average ROI:
{avg_roi if avg_roi is not None else "N/A"}

Thesis:
{card.get("final_thesis")}
""".strip()


def format_top_final(limit=10):
    cards = get_top_final(limit=limit)

    if not cards:
        return "No Oracle final fusion cards found."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_final_card(card, rank=i)
        for i, card in enumerate(cards[:int(limit)], start=1)
    )


def diagnostics():
    payload = run_final_fusion(limit=50)

    return {
        "module": "oracle_final_fusion",
        "status": "ok",
        "cards": payload.get("count"),
        "top": [
            {
                "ticker": c.get("ticker"),
                "final_recommendation": c.get("final_recommendation"),
                "final_grade": c.get("final_grade"),
                "final_score": c.get("final_score"),
                "similarity_adjustment": c.get("similarity_adjustment"),
            }
            for c in payload.get("cards", [])[:5]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top_final(limit=5))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-043 INSTALLED")
print(" Evidence + Similarity Fusion")
print("===================================")
print()
print("Created:")
print(" oracle_final_fusion.py")
print()
print("Test:")
print(" python oracle_final_fusion.py")