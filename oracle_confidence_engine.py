
"""
ORACLE-036 — Confidence Engine

Purpose:
- Add Oracle confidence score to each opportunity.
"""

def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def calculate_confidence(market):

    score = float(market.get("oracle_score", 0))
    edge = abs(float(market.get("oracle_edge", 0)))
    volume = float(market.get("volume", 0))
    liquidity = float(market.get("liquidity", 0))

    confidence = 40.0

    confidence += score * 0.35
    confidence += min(edge * 4, 15)
    confidence += min(volume / 10000, 10)
    confidence += min(liquidity / 5000, 10)

    market = dict(market)
    market["oracle_confidence"] = round(clamp(confidence), 2)

    return market


def apply_confidence(markets):

    return [calculate_confidence(m) for m in markets]
