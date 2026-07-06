def clamp(value, low=1, high=99):
    return max(low, min(high, round(value, 1)))


def base_probability_from_market(market_price):
    return clamp(market_price)


def category_base_adjustment(category):
    category = str(category or "").lower()

    if category == "crypto":
        return 0

    if category == "sports":
        return 0

    if category == "weather":
        return 0

    if category == "politics":
        return 0

    if category == "entertainment":
        return 0

    if category == "tesla_spacex":
        return 0

    return 0


def probability_from_signals(
    market_price,
    category="general",
    spread=0,
    volume_24h=0,
    volume_total=0,
    move=0,
    source_strength="None",
    side="BUY YES",
):
    probability = base_probability_from_market(market_price)

    reasons = []

    probability += category_base_adjustment(category)

    if spread > 0 and spread <= 3:
        probability += 2
        reasons.append("Tight spread supports price reliability")
    elif spread > 6:
        probability -= 4
        reasons.append("Wide spread reduces confidence")

    if volume_24h >= 1000 or volume_total >= 5000:
        probability += 3
        reasons.append("Strong liquidity supports signal")
    elif volume_24h >= 100 or volume_total >= 1000:
        probability += 2
        reasons.append("Usable liquidity supports signal")
    else:
        probability -= 2
        reasons.append("Low liquidity reduces confidence")

    if move >= 5:
        probability += 4
        reasons.append("Strong recent repricing")
    elif move >= 2:
        probability += 2
        reasons.append("Recent movement detected")

    if source_strength == "Strong":
        probability += 5
        reasons.append("Strong outside-source confirmation")
    elif source_strength == "Moderate":
        probability += 3
        reasons.append("Moderate outside-source confirmation")
    elif source_strength == "Weak":
        probability += 1
        reasons.append("Weak outside-source confirmation")
    else:
        probability -= 3
        reasons.append("No outside-source confirmation")

    if side == "BUY NO":
        probability = 100 - probability
        reasons.append("Converted probability for BUY NO side")

    return {
        "bot_probability": clamp(probability),
        "probability_reasons": reasons,
    }


if __name__ == "__main__":
    result = probability_from_signals(
        market_price=52,
        category="crypto",
        spread=2,
        volume_24h=5000,
        volume_total=10000,
        move=4,
        source_strength="Moderate",
        side="BUY YES",
    )

    print(result)