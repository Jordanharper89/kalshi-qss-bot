def mlb_probability(
    market_price,

    pitcher_score=50,
    lineup_score=50,
    weather_score=50,
    bullpen_score=50,
    odds_score=50,
):

    probability = market_price

    reasons = []

    # PITCHERS (30%)

    probability += ((pitcher_score - 50) * 0.30)

    # LINEUPS (30%)

    probability += ((lineup_score - 50) * 0.30)

    # WEATHER (15%)

    probability += ((weather_score - 50) * 0.15)

    # BULLPENS (10%)

    probability += ((bullpen_score - 50) * 0.10)

    # ODDS / MARKET (15%)

    probability += ((odds_score - 50) * 0.15)

    if pitcher_score > 60:
        reasons.append("Pitching edge")

    if lineup_score > 60:
        reasons.append("Lineup edge")

    if weather_score > 60:
        reasons.append("Weather edge")

    if bullpen_score > 60:
        reasons.append("Bullpen edge")

    if odds_score > 60:
        reasons.append("Odds market agreement")

    probability = round(probability)

    probability = max(1, min(99, probability))

    return {
        "bot_probability": probability,
        "reasons": reasons,
    }


if __name__ == "__main__":

    result = mlb_probability(
        market_price=52,

        pitcher_score=75,
        lineup_score=80,
        weather_score=70,
        bullpen_score=60,
        odds_score=72,
    )

    print(result)