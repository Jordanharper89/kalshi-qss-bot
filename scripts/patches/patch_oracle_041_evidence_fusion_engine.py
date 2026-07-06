from pathlib import Path

TARGET = Path("oracle_evidence_fusion.py")

TARGET.write_text(r'''
"""
ORACLE-041 — Evidence Fusion Engine

Purpose:
- Convert Oracle market intelligence cards into evidence-based recommendations
- Score positive and negative evidence separately
- Produce evidence_score, confidence, recommendation, grade, and trade thesis
- Designed to improve downstream ranking and continuous intelligence

Safe:
- No trading
- No orders
"""

import json
import time
from pathlib import Path
from math import isfinite

INTELLIGENCE_FILE = Path("oracle_market_intelligence.json")
EVIDENCE_FILE = Path("oracle_evidence_fusion.json")


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


def evidence_item(name, points, reason, polarity="positive"):
    return {
        "name": name,
        "points": round(safe_float(points), 2),
        "reason": reason,
        "polarity": polarity,
    }


def get_raw_market(card):
    raw = card.get("raw_market")
    if isinstance(raw, dict):
        return raw

    raw = card.get("raw")
    if isinstance(raw, dict):
        rm = raw.get("raw_market")
        if isinstance(rm, dict):
            return rm

    return {}


def get_event(card):
    raw_market = get_raw_market(card)
    event = raw_market.get("event")
    return event if isinstance(event, dict) else {}


def source_quality(card):
    return safe_float(card.get("source_quality") or card.get("raw", {}).get("source_quality"))


def spread(card):
    return safe_float(card.get("spread") or card.get("raw", {}).get("spread"))


def liquidity_score(card):
    return safe_float(card.get("liquidity_score") or card.get("raw", {}).get("liquidity_score"))


def price_quality(card):
    return safe_float(card.get("price_quality") or card.get("raw", {}).get("price_quality"))


def research_score(card):
    return safe_float(card.get("research_score") or card.get("raw", {}).get("research_score"))


def confidence(card):
    return safe_float(card.get("confidence") or card.get("raw", {}).get("confidence"))


def edge(card):
    return safe_float(card.get("edge") or card.get("raw", {}).get("edge"))


def market_price(card):
    return safe_float(card.get("market_price") or card.get("raw", {}).get("market_price"))


def fair_value(card):
    return safe_float(card.get("fair_value") or card.get("raw", {}).get("fair_value"))


def provider_count(card):
    providers = card.get("providers_needed") or card.get("raw", {}).get("providers_needed") or []
    if isinstance(providers, list):
        return len(providers)
    return 0


def settlement_source_count(card):
    event = get_event(card)
    sources = event.get("settlement_sources")
    if isinstance(sources, list):
        return len(sources)
    return 0


def classify_domain(card):
    cls = card.get("classification") or card.get("raw", {}).get("classification") or {}
    if isinstance(cls, dict):
        return cls.get("domain", "unknown"), cls.get("subtype", "general")
    return "unknown", "general"


def build_evidence(card):
    positive = []
    negative = []

    e = edge(card)
    c = confidence(card)
    r = research_score(card)
    sq = source_quality(card)
    lq = liquidity_score(card)
    pq = price_quality(card)
    sp = spread(card)
    providers = provider_count(card)
    settle_sources = settlement_source_count(card)
    price = market_price(card)

    if abs(e) >= 0.08:
        positive.append(evidence_item("Large fair-value gap", 18, f"Estimated edge is {round(e*100,2)}%."))
    elif abs(e) >= 0.05:
        positive.append(evidence_item("Meaningful fair-value gap", 12, f"Estimated edge is {round(e*100,2)}%."))
    elif abs(e) >= 0.03:
        positive.append(evidence_item("Small fair-value gap", 6, f"Estimated edge is {round(e*100,2)}%."))
    else:
        negative.append(evidence_item("Weak edge", -10, "Estimated fair-value gap is below preferred threshold.", "negative"))

    if c >= 85:
        positive.append(evidence_item("High confidence", 16, f"Oracle confidence is {c}."))
    elif c >= 75:
        positive.append(evidence_item("Good confidence", 10, f"Oracle confidence is {c}."))
    elif c >= 65:
        positive.append(evidence_item("Acceptable confidence", 4, f"Oracle confidence is {c}."))
    else:
        negative.append(evidence_item("Low confidence", -16, f"Oracle confidence is only {c}.", "negative"))

    if r >= 85:
        positive.append(evidence_item("Strong research score", 14, f"Research score is {r}."))
    elif r >= 75:
        positive.append(evidence_item("Good research score", 8, f"Research score is {r}."))
    elif r < 60:
        negative.append(evidence_item("Weak research support", -10, f"Research score is only {r}.", "negative"))

    if sq >= 90:
        positive.append(evidence_item("Excellent settlement/source quality", 12, "Market has strong listed settlement sources."))
    elif sq >= 75:
        positive.append(evidence_item("Good settlement/source quality", 7, "Settlement/source quality is acceptable."))
    elif sq < 60:
        negative.append(evidence_item("Weak source quality", -8, "Settlement/source quality is limited.", "negative"))

    if lq >= 80:
        positive.append(evidence_item("Strong activity/liquidity profile", 10, f"Liquidity score is {lq}."))
    elif lq >= 65:
        positive.append(evidence_item("Acceptable activity profile", 5, f"Liquidity score is {lq}."))
    else:
        negative.append(evidence_item("Thin market activity", -12, f"Liquidity score is only {lq}.", "negative"))

    if pq >= 85:
        positive.append(evidence_item("Strong price quality", 10, "Bid/ask structure is tradable."))
    elif pq >= 70:
        positive.append(evidence_item("Acceptable price quality", 5, "Price structure is usable."))
    else:
        negative.append(evidence_item("Poor price quality", -12, "Bid/ask structure is weak or wide.", "negative"))

    if sp > 0.15:
        negative.append(evidence_item("Wide spread", -14, f"Spread is {sp}.", "negative"))
    elif sp > 0.08:
        negative.append(evidence_item("Moderate spread risk", -7, f"Spread is {sp}.", "negative"))
    elif sp > 0 and sp <= 0.05:
        positive.append(evidence_item("Tight spread", 6, f"Spread is {sp}."))

    if providers >= 7:
        positive.append(evidence_item("Multiple provider types available", 7, f"{providers} provider types are mapped."))
    elif providers <= 3:
        negative.append(evidence_item("Limited provider coverage", -6, f"Only {providers} provider types are mapped.", "negative"))

    if settle_sources >= 8:
        positive.append(evidence_item("Many settlement sources", 6, f"{settle_sources} settlement sources listed."))
    elif settle_sources <= 1:
        negative.append(evidence_item("Few settlement sources", -5, f"{settle_sources} settlement sources listed.", "negative"))

    if price <= 0.02 or price >= 0.98:
        negative.append(evidence_item("Extreme price risk", -10, f"Market price is {price}.", "negative"))

    raw_market = get_raw_market(card)
    close_time = str(raw_market.get("close_time") or raw_market.get("expiration_time") or "")
    if any(year in close_time for year in ["2035", "2040", "2045", "2099"]):
        negative.append(evidence_item("Long-dated market risk", -12, f"Market closes far in the future: {close_time}.", "negative"))
    elif any(year in close_time for year in ["2030", "2031"]):
        negative.append(evidence_item("Moderately long-dated market", -6, f"Market closes in {close_time}.", "negative"))

    return positive, negative


def grade_from_evidence(score, recommendation, confidence_value):
    score = safe_float(score)
    recommendation = str(recommendation or "PASS").upper()
    confidence_value = safe_float(confidence_value)

    if recommendation in ("BUY YES", "BUY NO") and score >= 82 and confidence_value >= 82:
        return "A+"
    if recommendation in ("BUY YES", "BUY NO") and score >= 75 and confidence_value >= 78:
        return "A"
    if recommendation in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO") and score >= 68 and confidence_value >= 74:
        return "A-"
    if score >= 60:
        return "B+"
    if score >= 52:
        return "B"
    if score >= 45:
        return "B-"
    if score >= 35:
        return "C"
    return "PASS"


def recommendation_from_evidence(net_points, card):
    e = edge(card)
    c = confidence(card)

    if net_points >= 65 and c >= 82 and abs(e) >= 0.06:
        return "BUY YES" if e > 0 else "BUY NO"

    if net_points >= 48 and c >= 74 and abs(e) >= 0.035:
        return "LEAN YES" if e > 0 else "LEAN NO"

    if net_points >= 35:
        return "WATCH"

    return "PASS"


def analyze_evidence(card):
    positive, negative = build_evidence(card)

    pos_total = sum(x["points"] for x in positive)
    neg_total = sum(abs(x["points"]) for x in negative)
    net = pos_total - neg_total

    evidence_score = clamp(50 + net, 0, 100)

    rec = recommendation_from_evidence(evidence_score, card)
    grade = grade_from_evidence(evidence_score, rec, confidence(card))

    fused = dict(card)
    fused["evidence_positive"] = positive
    fused["evidence_negative"] = negative
    fused["evidence_positive_points"] = round(pos_total, 2)
    fused["evidence_negative_points"] = round(neg_total, 2)
    fused["evidence_net_points"] = round(net, 2)
    fused["evidence_score"] = round(evidence_score, 2)
    fused["fused_recommendation"] = rec
    fused["fused_grade"] = grade
    fused["fused_rank_score"] = fused_rank_score(fused)
    fused["trade_thesis"] = build_trade_thesis(fused)
    fused["created_at"] = now()

    return fused


def fused_rank_score(card):
    rec = str(card.get("fused_recommendation") or "PASS").upper()
    score = safe_float(card.get("evidence_score"))
    c = confidence(card)
    e = abs(edge(card))

    rank = score * 0.55 + c * 0.25 + min(e * 300, 20)

    if rec in ("BUY YES", "BUY NO"):
        rank += 20
    elif rec in ("LEAN YES", "LEAN NO"):
        rank += 10
    elif rec == "PASS":
        rank -= 20

    return round(clamp(rank), 2)


def build_trade_thesis(card):
    rec = card.get("fused_recommendation")
    grade = card.get("fused_grade")
    ticker = card.get("ticker")
    e = round(edge(card) * 100, 2)

    pos = card.get("evidence_positive", [])[:4]
    neg = card.get("evidence_negative", [])[:3]

    lines = []
    lines.append(f"{ticker}: {rec} ({grade})")
    lines.append(f"Estimated edge: {e}%")
    lines.append("")

    if pos:
        lines.append("Supporting evidence:")
        for item in pos:
            lines.append(f"• {item['name']}: {item['reason']}")

    if neg:
        lines.append("")
        lines.append("Risks:")
        for item in neg:
            lines.append(f"• {item['name']}: {item['reason']}")

    return "\n".join(lines)


def load_cards(limit=50):
    if not INTELLIGENCE_FILE.exists():
        try:
            from oracle_market_intelligence import analyze_universe
            analyze_universe(limit=500, top=50)
        except Exception:
            return []

    try:
        data = json.loads(INTELLIGENCE_FILE.read_text(encoding="utf-8"))
        cards = data.get("cards", [])
        return cards[:int(limit)] if isinstance(cards, list) else []
    except Exception:
        return []


def fuse_cards(cards=None, limit=50):
    cards = cards if cards is not None else load_cards(limit=limit)

    fused = [analyze_evidence(card) for card in cards or []]

    fused.sort(
        key=lambda x: (
            x.get("fused_rank_score", 0),
            x.get("evidence_score", 0),
            abs(safe_float(x.get("edge"))),
        ),
        reverse=True,
    )

    payload = {
        "version": "ORACLE-041",
        "updated_at": now(),
        "count": len(fused),
        "cards": fused,
    }

    EVIDENCE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_top_fused(limit=10):
    if not EVIDENCE_FILE.exists():
        fuse_cards(limit=max(50, limit))

    try:
        data = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
        cards = data.get("cards", [])
        return cards[:int(limit)]
    except Exception:
        return []


def format_fused_card(card, rank=None):
    rank_line = f"Rank #{rank}" if rank else "Evidence Card"

    positives = card.get("evidence_positive", [])[:4]
    negatives = card.get("evidence_negative", [])[:3]

    pos_text = "\n".join(f"• +{x.get('points')} {x.get('name')}: {x.get('reason')}" for x in positives) or "None"
    neg_text = "\n".join(f"• -{abs(safe_float(x.get('points')))} {x.get('name')}: {x.get('reason')}" for x in negatives) or "None"

    return f"""
🧠 ORACLE EVIDENCE FUSION

{rank_line}

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Recommendation:
{card.get("fused_recommendation")}

Grade:
{card.get("fused_grade")}

Evidence Score:
{card.get("evidence_score")}

Rank Score:
{card.get("fused_rank_score")}

Market Price:
{card.get("market_price")}

Fair Value:
{card.get("fair_value")}

Edge:
{round(safe_float(card.get("edge")) * 100, 2)}%

Confidence:
{card.get("confidence")}

Positive Evidence:
{pos_text}

Risk Evidence:
{neg_text}

Trade Thesis:
{card.get("trade_thesis")}
""".strip()


def format_top_fused(limit=10):
    cards = get_top_fused(limit=limit)

    if not cards:
        return "No Oracle evidence fusion cards found."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_fused_card(card, rank=i)
        for i, card in enumerate(cards[:int(limit)], start=1)
    )


def diagnostics():
    payload = fuse_cards(limit=50)

    return {
        "module": "oracle_evidence_fusion",
        "status": "ok",
        "cards": payload.get("count"),
        "top": [
            {
                "ticker": c.get("ticker"),
                "recommendation": c.get("fused_recommendation"),
                "grade": c.get("fused_grade"),
                "evidence_score": c.get("evidence_score"),
                "rank_score": c.get("fused_rank_score"),
            }
            for c in payload.get("cards", [])[:5]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top_fused(limit=5))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-041 INSTALLED")
print(" Evidence Fusion Engine")
print("===================================")
print()
print("Created:")
print(" oracle_evidence_fusion.py")
print()
print("Test:")
print(" python oracle_evidence_fusion.py")