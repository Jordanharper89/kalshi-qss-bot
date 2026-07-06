"""
ORACLE-033 — Adaptive Opportunity Ranking

Purpose:
- Rank live Oracle opportunities using:
  1. ORACLE-028 intelligence score
  2. ORACLE-032 self-learning multiplier
- Boost setups that historically worked
- Reduce setups that historically performed poorly
- Safe module: does not execute trades
"""

from oracle_opportunity_intelligence import analyze_opportunity
from oracle_self_learning import recommend_multiplier


def adaptive_scorecard(opportunity):
    card = analyze_opportunity(opportunity)

    multiplier = recommend_multiplier(
        grade=card.get("grade"),
        edge=card.get("edge", 0),
        confidence=card.get("confidence", 0),
    )

    base_score = float(card.get("overall_score", 0))
    adaptive_score = round(base_score * multiplier, 2)

    card["base_score"] = base_score
    card["learning_multiplier"] = multiplier
    card["adaptive_score"] = adaptive_score

    if multiplier > 1:
        card["learning_note"] = "Boosted by historical performance"
    elif multiplier < 1:
        card["learning_note"] = "Reduced by historical performance"
    else:
        card["learning_note"] = "Neutral historical adjustment"

    return card


def rank_opportunities(opportunities, limit=10):
    cards = [adaptive_scorecard(item) for item in opportunities or []]

    cards.sort(
        key=lambda x: (
            x.get("adaptive_score", 0),
            x.get("overall_score", 0),
            x.get("confidence", 0),
        ),
        reverse=True,
    )

    return cards[:int(limit)]


def format_adaptive_card(card, rank=None):
    label = f"Rank #{rank}" if rank else "Opportunity"

    return f"""
🧠 ORACLE ADAPTIVE RANKING

{label}

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Side:
{card.get("side")}

Grade:
{card.get("grade")}

Base Score:
{card.get("base_score")}/100

Learning Multiplier:
{xformat(card.get("learning_multiplier"))}

Adaptive Score:
{card.get("adaptive_score")}/100

Risk:
{card.get("risk")}

Edge:
{card.get("edge")}

Confidence:
{card.get("confidence")}

Learning Note:
{card.get("learning_note")}

Reason:
{card.get("reason")}
""".strip()


def xformat(value):
    try:
        return f"{float(value):.2f}x"
    except Exception:
        return str(value)


def format_ranked_opportunities(cards):
    if not cards:
        return "No adaptive opportunities found."

    chunks = []

    for i, card in enumerate(cards, start=1):
        chunks.append(format_adaptive_card(card, rank=i))

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(chunks)


def diagnostics():
    sample = [
        {
            "ticker": "TEST-ADAPT-1",
            "title": "Adaptive Ranking Test 1",
            "side": "YES",
            "edge": 8.4,
            "confidence": 92,
            "fair_value": 0.68,
            "market_price": 0.59,
            "volume": 42000,
            "age_seconds": 40,
            "providers": ["oracle", "cache", "research"],
        },
        {
            "ticker": "TEST-ADAPT-2",
            "title": "Adaptive Ranking Test 2",
            "side": "NO",
            "edge": 4.2,
            "confidence": 74,
            "fair_value": 0.42,
            "market_price": 0.47,
            "volume": 2500,
            "age_seconds": 160,
            "providers": ["oracle"],
        },
    ]

    ranked = rank_opportunities(sample)

    return {
        "module": "oracle_adaptive_ranking",
        "status": "ok",
        "ranked": len(ranked),
        "top_ticker": ranked[0]["ticker"] if ranked else None,
        "top_adaptive_score": ranked[0]["adaptive_score"] if ranked else None,
    }


if __name__ == "__main__":
    print(diagnostics())
    print()
    print(format_ranked_opportunities(rank_opportunities([
        {
            "ticker": "TEST-ADAPT-1",
            "title": "Adaptive Ranking Test 1",
            "side": "YES",
            "edge": 8.4,
            "confidence": 92,
            "fair_value": 0.68,
            "market_price": 0.59,
            "volume": 42000,
            "age_seconds": 40,
            "providers": ["oracle", "cache", "research"],
        }
    ])))
