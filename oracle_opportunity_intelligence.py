"""
ORACLE-028 — Opportunity Intelligence Engine

Purpose:
- Turn raw Oracle opportunities into analyst-style scorecards
- Explain WHY an opportunity is strong or weak
- Break opportunity quality into components:
  edge, confidence, freshness, provider agreement, data quality, risk
- Safe add-on module. Does not execute trades.
"""

import time
from math import isfinite


def clamp(value, low=0.0, high=100.0):
    try:
        value = float(value)
    except Exception:
        return low

    if not isfinite(value):
        return low

    return max(low, min(high, value))


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if not isfinite(value):
            return default
        return value
    except Exception:
        return default


def grade_from_score(score):
    score = clamp(score)

    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 85:
        return "A-"
    if score >= 80:
        return "B+"
    if score >= 75:
        return "B"
    if score >= 70:
        return "B-"
    if score >= 60:
        return "C"
    return "PASS"


def risk_from_score(score):
    score = clamp(score)

    if score >= 85:
        return "LOW"
    if score >= 70:
        return "MEDIUM"
    return "HIGH"


def normalize_opportunity(raw):
    raw = raw or {}

    ticker = (
        raw.get("ticker")
        or raw.get("market_ticker")
        or raw.get("id")
        or "UNKNOWN"
    )

    title = (
        raw.get("title")
        or raw.get("market_title")
        or raw.get("name")
        or ticker
    )

    side = str(raw.get("side") or raw.get("recommendation") or "WATCH").upper()

    edge = safe_float(
        raw.get("edge")
        or raw.get("edge_score")
        or raw.get("expected_edge")
        or raw.get("edge_pct")
        or 0
    )

    confidence = safe_float(
        raw.get("confidence")
        or raw.get("confidence_score")
        or raw.get("probability_confidence")
        or 50
    )

    fair_value = safe_float(
        raw.get("fair_value")
        or raw.get("oracle_fair_value")
        or raw.get("fv")
        or 0
    )

    market_price = safe_float(
        raw.get("price")
        or raw.get("market_price")
        or raw.get("yes_price")
        or raw.get("current_price")
        or 0
    )

    volume = safe_float(raw.get("volume") or raw.get("liquidity") or 0)
    age_seconds = safe_float(raw.get("age_seconds") or raw.get("data_age_seconds") or 0)

    providers = raw.get("providers") or raw.get("provider_count") or []
    if isinstance(providers, list):
        provider_count = len(providers)
    else:
        provider_count = safe_float(providers, 0)

    return {
        "ticker": str(ticker),
        "title": str(title),
        "side": side,
        "edge": edge,
        "confidence": confidence,
        "fair_value": fair_value,
        "market_price": market_price,
        "volume": volume,
        "age_seconds": age_seconds,
        "provider_count": provider_count,
        "raw": raw,
    }


def score_edge(edge):
    edge = abs(safe_float(edge))
    return clamp(edge * 10, 0, 100)


def score_confidence(confidence):
    return clamp(confidence)


def score_freshness(age_seconds):
    age_seconds = safe_float(age_seconds)

    if age_seconds <= 0:
        return 75

    if age_seconds <= 30:
        return 100
    if age_seconds <= 60:
        return 95
    if age_seconds <= 180:
        return 85
    if age_seconds <= 300:
        return 75
    if age_seconds <= 600:
        return 60
    return 40


def score_provider_agreement(provider_count):
    provider_count = safe_float(provider_count)

    if provider_count >= 5:
        return 100
    if provider_count == 4:
        return 92
    if provider_count == 3:
        return 84
    if provider_count == 2:
        return 72
    if provider_count == 1:
        return 55
    return 45


def score_liquidity(volume):
    volume = safe_float(volume)

    if volume >= 100000:
        return 100
    if volume >= 50000:
        return 90
    if volume >= 10000:
        return 80
    if volume >= 2500:
        return 70
    if volume >= 500:
        return 60
    if volume > 0:
        return 50
    return 45


def score_price_gap(fair_value, market_price):
    fair_value = safe_float(fair_value)
    market_price = safe_float(market_price)

    if fair_value <= 0 or market_price <= 0:
        return 50

    gap = abs(fair_value - market_price)
    return clamp(gap * 100, 0, 100)


def build_strengths(scores, item):
    strengths = []

    if scores["edge"] >= 80:
        strengths.append("Strong edge versus current market price")
    elif scores["edge"] >= 60:
        strengths.append("Moderate edge detected")

    if scores["confidence"] >= 85:
        strengths.append("High Oracle confidence")
    elif scores["confidence"] >= 70:
        strengths.append("Acceptable confidence")

    if scores["freshness"] >= 90:
        strengths.append("Fresh data")
    elif scores["freshness"] < 60:
        strengths.append("Older data, watch for refresh")

    if scores["provider_agreement"] >= 84:
        strengths.append("Multiple data sources support the read")
    elif scores["provider_agreement"] < 60:
        strengths.append("Limited provider confirmation")

    if scores["liquidity"] >= 75:
        strengths.append("Good liquidity/volume profile")
    elif scores["liquidity"] < 55:
        strengths.append("Thin liquidity risk")

    return strengths or ["No major strength detected yet"]


def build_warnings(scores, item):
    warnings = []

    if scores["confidence"] < 65:
        warnings.append("Confidence is below preferred range")

    if scores["freshness"] < 60:
        warnings.append("Data may be stale")

    if scores["provider_agreement"] < 60:
        warnings.append("Low provider agreement")

    if scores["liquidity"] < 55:
        warnings.append("Liquidity may be weak")

    if scores["edge"] < 50:
        warnings.append("Edge is not strong enough yet")

    return warnings


def build_reason(scorecard):
    strengths = scorecard.get("strengths", [])
    warnings = scorecard.get("warnings", [])

    lines = []

    for item in strengths[:4]:
        lines.append(f"• {item}")

    for item in warnings[:3]:
        lines.append(f"⚠ {item}")

    return "\n".join(lines) if lines else "No reason generated."


def analyze_opportunity(raw):
    item = normalize_opportunity(raw)

    scores = {
        "edge": score_edge(item["edge"]),
        "confidence": score_confidence(item["confidence"]),
        "freshness": score_freshness(item["age_seconds"]),
        "provider_agreement": score_provider_agreement(item["provider_count"]),
        "liquidity": score_liquidity(item["volume"]),
        "price_gap": score_price_gap(item["fair_value"], item["market_price"]),
    }

    data_quality = clamp(
        scores["freshness"] * 0.35
        + scores["provider_agreement"] * 0.35
        + scores["liquidity"] * 0.30
    )

    overall = clamp(
        scores["edge"] * 0.30
        + scores["confidence"] * 0.25
        + data_quality * 0.20
        + scores["price_gap"] * 0.15
        + scores["freshness"] * 0.10
    )

    grade = grade_from_score(overall)
    risk = risk_from_score((data_quality * 0.55) + (scores["confidence"] * 0.45))

    scorecard = {
        "ticker": item["ticker"],
        "title": item["title"],
        "side": item["side"],
        "overall_score": round(overall, 2),
        "grade": grade,
        "risk": risk,
        "edge": item["edge"],
        "confidence": round(item["confidence"], 2),
        "fair_value": item["fair_value"],
        "market_price": item["market_price"],
        "scores": {
            **{k: round(v, 2) for k, v in scores.items()},
            "data_quality": round(data_quality, 2),
        },
        "strengths": build_strengths(scores, item),
        "warnings": build_warnings(scores, item),
        "created_at": time.time(),
        "raw": item["raw"],
    }

    scorecard["reason"] = build_reason(scorecard)
    return scorecard


def analyze_opportunities(opportunities, min_grade=None, limit=None):
    cards = [analyze_opportunity(item) for item in (opportunities or [])]
    cards.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    if min_grade:
        allowed = {
            "A+": 95,
            "A": 90,
            "A-": 85,
            "B+": 80,
            "B": 75,
            "B-": 70,
            "C": 60,
        }
        floor = allowed.get(str(min_grade).upper(), 0)
        cards = [c for c in cards if c.get("overall_score", 0) >= floor]

    if limit:
        cards = cards[:int(limit)]

    return cards


def format_scorecard(card):
    scores = card.get("scores", {})

    return f"""
🧠 ORACLE INTELLIGENCE SCORECARD

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Side:
{card.get("side")}

Grade:
{card.get("grade")}

Overall Score:
{card.get("overall_score")}/100

Risk:
{card.get("risk")}

Edge:
{card.get("edge")}

Confidence:
{card.get("confidence")}

Component Scores:
• Edge: {scores.get("edge")}/100
• Confidence: {scores.get("confidence")}/100
• Data Quality: {scores.get("data_quality")}/100
• Freshness: {scores.get("freshness")}/100
• Provider Agreement: {scores.get("provider_agreement")}/100
• Liquidity: {scores.get("liquidity")}/100

Reason:
{card.get("reason")}
""".strip()


def diagnostics():
    sample = {
        "ticker": "TEST-MARKET",
        "title": "Test Market",
        "side": "YES",
        "edge": 7.5,
        "confidence": 88,
        "fair_value": 0.62,
        "market_price": 0.54,
        "volume": 25000,
        "age_seconds": 45,
        "providers": ["cache", "research", "provider"],
    }

    card = analyze_opportunity(sample)

    return {
        "module": "oracle_opportunity_intelligence",
        "status": "ok",
        "sample_grade": card["grade"],
        "sample_score": card["overall_score"],
        "sample_risk": card["risk"],
    }


if __name__ == "__main__":
    print(diagnostics())
    print()
    print(format_scorecard(analyze_opportunity({
        "ticker": "TEST-MARKET",
        "title": "Example Oracle Opportunity",
        "side": "YES",
        "edge": 8.4,
        "confidence": 91,
        "fair_value": 0.68,
        "market_price": 0.59,
        "volume": 42000,
        "age_seconds": 38,
        "providers": ["oracle", "cache", "research"],
    })))
