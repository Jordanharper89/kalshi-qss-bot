
"""
ORACLE-033 — Opportunity Ranking Engine

Purpose:
- Score normalized Oracle markets.
- Return highest-quality opportunities.
"""

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_market(market):

    score = 50.0

    volume = float(market.get("volume", 0))
    liquidity = float(market.get("liquidity", 0))
    yes = float(market.get("yes_price", 0))

    if 20 <= yes <= 80:
        score += 10

    score += min(volume / 5000.0, 20)
    score += min(liquidity / 2000.0, 20)

    score = clamp(score)

    market["oracle_score"] = round(score, 2)

    if score >= 90:
        market["grade"] = "A+"
    elif score >= 85:
        market["grade"] = "A"
    elif score >= 80:
        market["grade"] = "A-"
    elif score >= 75:
        market["grade"] = "B+"
    elif score >= 70:
        market["grade"] = "B"
    else:
        market["grade"] = "C"

    return market


def rank_markets(markets):

    ranked = []

    for market in markets.values():
        ranked.append(score_market(dict(market)))

    ranked.sort(
        key=lambda m: m.get("oracle_score", 0),
        reverse=True,
    )

    return ranked
