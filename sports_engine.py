from sport_router import detect_sport
from sports.mlb_engine import mlb_probability
from sports.soccer_engine import soccer_probability


def generic_sports_probability(
    market_price,
    spread=0,
    move=0,
    volume_24h=0,
):
    probability = market_price
    reasons = []

    if spread <= 3:
        probability += 2
        reasons.append("Tight spread")

    if move >= 3:
        probability += 2
        reasons.append("Market momentum")

    if volume_24h >= 100:
        probability += 1
        reasons.append("Volume confirmation")

    probability = max(1, min(99, round(probability)))

    return {
        "bot_probability": probability,
        "valid": True,
        "sport": "generic_sports",
        "component_scores": {},
        "reasons": reasons,
    }


def sports_probability(
    market_price,
    market_title="",
    spread=0,
    move=0,
    volume_24h=0,
):
    sport = detect_sport(market_title)

    if sport == "mlb":
        return mlb_probability(
            market_price=market_price,
            starter_confirmed=True,
            no_tbd=True,
            no_opener=True,
            lineup_confirmed=True,
            pitcher_quality=65,
            top_order_strength=65,
            stars_active=True,
            market_steam=move >= 3,
            fair_value_edge=5 if volume_24h >= 100 else 0,
        )

    if sport == "soccer":
        return soccer_probability(
            market_price=market_price,
            lineup_score=58,
            injury_score=55,
            form_score=58,
            odds_score=58 if volume_24h >= 100 else 52,
            motivation_score=55,
        )

    return generic_sports_probability(
        market_price=market_price,
        spread=spread,
        move=move,
        volume_24h=volume_24h,
    )


if __name__ == "__main__":
    tests = [
        "World Cup Best Performing Host Nation",
        "Pro Baseball Player of the Month",
        "AP Pro Football Defensive Player Of The Year",
        "Pro Basketball Western Conference Champion",
        "NHL Jack Adams Award",
        "UFC Method of Finish",
        "Alexander Zverev tennis match",
    ]

    for test in tests:
        print("-" * 60)
        print(test)
        print(
            sports_probability(
                market_price=52,
                market_title=test,
                spread=2,
                move=4,
                volume_24h=1000,
            )
        )