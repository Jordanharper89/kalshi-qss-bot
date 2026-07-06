
"""
ORACLE-038 — Risk Engine

Purpose:
Assign a standardized Oracle risk profile to every opportunity.
"""


def calculate_risk(market):

    market = dict(market)

    confidence = float(market.get("oracle_confidence", 0))
    edge = abs(float(market.get("oracle_edge", 0)))
    liquidity = float(market.get("liquidity", 0))
    volume = float(market.get("volume", 0))

    score = 100.0

    if confidence < 90:
        score -= (90 - confidence) * 0.40

    if edge < 2:
        score -= (2 - edge) * 8

    if liquidity < 1000:
        score -= 10

    if volume < 5000:
        score -= 10

    score = max(0.0, min(100.0, score))

    if score >= 90:
        level = "VERY LOW"
    elif score >= 80:
        level = "LOW"
    elif score >= 65:
        level = "MEDIUM"
    elif score >= 50:
        level = "HIGH"
    else:
        level = "VERY HIGH"

    market["oracle_risk_score"] = round(score, 2)
    market["oracle_risk"] = level

    return market


def apply_risk(markets):
    return [calculate_risk(m) for m in markets]
