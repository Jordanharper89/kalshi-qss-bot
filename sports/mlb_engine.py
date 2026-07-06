def clamp(value, low=1, high=99):
    return max(low, min(high, round(value)))


def score_pitchers(
    starter_confirmed=True,
    no_tbd=True,
    no_opener=True,
    pitcher_quality=50,
):
    if not starter_confirmed or not no_tbd or not no_opener:
        return 0, ["Pitcher confirmation failed"]

    score = pitcher_quality
    reasons = ["Starting pitcher confirmed"]

    if score >= 70:
        reasons.append("Strong pitcher edge")
    elif score <= 40:
        reasons.append("Weak pitcher risk")

    return clamp(score, 0, 100), reasons


def score_lineups(
    lineup_confirmed=True,
    top_order_strength=50,
    stars_active=True,
):
    if not lineup_confirmed:
        return 0, ["Lineup not confirmed"]

    score = top_order_strength
    reasons = ["Top-order lineup confirmed"]

    if stars_active:
        score += 5
        reasons.append("Key bats active")
    else:
        score -= 10
        reasons.append("Missing star bats")

    return clamp(score, 0, 100), reasons


def score_weather(
    wind_out=False,
    wind_in=False,
    hot=False,
    cold=False,
    dome=False,
):
    score = 50
    reasons = []

    if wind_out:
        score += 15
        reasons.append("Wind out boost")

    if wind_in:
        score -= 10
        reasons.append("Wind in suppresses offense")

    if hot:
        score += 10
        reasons.append("Hot weather boost")

    if cold:
        score -= 8
        reasons.append("Cold weather suppresses offense")

    if dome:
        score += 3
        reasons.append("Dome removes weather risk")

    return clamp(score, 0, 100), reasons


def score_odds(
    market_steam=False,
    fair_value_edge=0,
):
    score = 50
    reasons = []

    if market_steam:
        score += 10
        reasons.append("Market steam detected")

    if fair_value_edge >= 10:
        score += 20
        reasons.append("Strong fair value edge")
    elif fair_value_edge >= 5:
        score += 10
        reasons.append("Fair value edge")

    return clamp(score, 0, 100), reasons


def mlb_probability(
    market_price,
    starter_confirmed=True,
    no_tbd=True,
    no_opener=True,
    lineup_confirmed=True,
    pitcher_quality=50,
    top_order_strength=50,
    stars_active=True,
    wind_out=False,
    wind_in=False,
    hot=False,
    cold=False,
    dome=False,
    market_steam=False,
    fair_value_edge=0,
):
    pitcher_score, pitcher_reasons = score_pitchers(
        starter_confirmed=starter_confirmed,
        no_tbd=no_tbd,
        no_opener=no_opener,
        pitcher_quality=pitcher_quality,
    )

    lineup_score, lineup_reasons = score_lineups(
        lineup_confirmed=lineup_confirmed,
        top_order_strength=top_order_strength,
        stars_active=stars_active,
    )

    weather_score, weather_reasons = score_weather(
        wind_out=wind_out,
        wind_in=wind_in,
        hot=hot,
        cold=cold,
        dome=dome,
    )

    odds_score, odds_reasons = score_odds(
        market_steam=market_steam,
        fair_value_edge=fair_value_edge,
    )

    if pitcher_score == 0 or lineup_score == 0:
        return {
            "bot_probability": 0,
            "valid": False,
            "reasons": pitcher_reasons + lineup_reasons,
        }

    probability = market_price
    probability += ((pitcher_score - 50) * 0.30)
    probability += ((lineup_score - 50) * 0.30)
    probability += ((weather_score - 50) * 0.15)
    probability += ((odds_score - 50) * 0.25)

    reasons = []
    reasons.extend(pitcher_reasons)
    reasons.extend(lineup_reasons)
    reasons.extend(weather_reasons)
    reasons.extend(odds_reasons)

    return {
        "bot_probability": clamp(probability),
        "valid": True,
        "component_scores": {
            "pitcher_score": pitcher_score,
            "lineup_score": lineup_score,
            "weather_score": weather_score,
            "odds_score": odds_score,
        },
        "reasons": reasons,
    }


if __name__ == "__main__":
    result = mlb_probability(
        market_price=52,
        starter_confirmed=True,
        no_tbd=True,
        no_opener=True,
        lineup_confirmed=True,
        pitcher_quality=75,
        top_order_strength=80,
        stars_active=True,
        wind_out=True,
        hot=True,
        market_steam=True,
        fair_value_edge=8,
    )

    print(result)