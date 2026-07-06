def clamp(value, low=1, high=99):
    return max(low, min(high, round(value)))


def soccer_probability(
    market_price,
    lineup_score=50,
    injury_score=50,
    form_score=50,
    odds_score=50,
    motivation_score=50,
):
    probability = market_price
    reasons = []

    probability += ((lineup_score - 50) * 0.25)
    probability += ((injury_score - 50) * 0.20)
    probability += ((form_score - 50) * 0.25)
    probability += ((odds_score - 50) * 0.20)
    probability += ((motivation_score - 50) * 0.10)

    if lineup_score > 60:
        reasons.append("Starting XI / lineup edge")

    if injury_score > 60:
        reasons.append("Injury availability edge")

    if form_score > 60:
        reasons.append("Recent form edge")

    if odds_score > 60:
        reasons.append("Odds market agreement")

    if motivation_score > 60:
        reasons.append("Motivation / group-stage edge")

    return {
        "bot_probability": clamp(probability),
        "valid": True,
        "sport": "soccer",
        "component_scores": {
            "lineup_score": lineup_score,
            "injury_score": injury_score,
            "form_score": form_score,
            "odds_score": odds_score,
            "motivation_score": motivation_score,
        },
        "reasons": reasons,
    }


if __name__ == "__main__":
    result = soccer_probability(
        market_price=52,
        lineup_score=70,
        injury_score=65,
        form_score=75,
        odds_score=72,
        motivation_score=60,
    )

    print(result)