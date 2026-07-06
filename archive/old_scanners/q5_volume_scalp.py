def q5_scalp_score(
    market_probability,
    bot_probability,
    spread,
    volume_24h,
    move,
    minutes_left=None,
    side=None,
):
    edge = bot_probability - market_probability
    score = 0
    reasons = []

    if side is None:
        side = "BUY YES" if edge >= 0 else "BUY NO"

    if edge >= 15:
        score += 25
        reasons.append("Massive scalp edge")
    elif edge >= 10:
        score += 18
        reasons.append("Strong scalp edge")
    elif edge >= 6:
        score += 12
        reasons.append("Usable scalp edge")
    else:
        reasons.append("Weak scalp edge")

    if spread <= 1:
        score += 20
        reasons.append("Very tight spread")
    elif spread <= 2:
        score += 14
        reasons.append("Tight spread")
    elif spread <= 4:
        score += 6
        reasons.append("Tradable spread")
    else:
        score -= 10
        reasons.append("Wide spread risk")

    if 40 <= market_probability <= 55:
        score += 25
        reasons.append("Prime scalp entry zone")
    elif 55 < market_probability <= 65:
        score += 15
        reasons.append("Good scalp entry zone")
    elif 25 <= market_probability < 40:
        score += 8
        reasons.append("Discount entry zone")
    elif market_probability > 70:
        score -= 15
        reasons.append("Chasing risk")
    elif market_probability < 15:
        score -= 5
        reasons.append("Low-probability lotto zone")

    if move >= 10:
        score += 18
        reasons.append("Strong repricing move")
    elif move >= 5:
        score += 10
        reasons.append("Momentum present")
    elif move >= 2:
        score += 5
        reasons.append("Small market movement")

    if volume_24h >= 300000:
        score += 12
        reasons.append("Heavy volume")
    elif volume_24h >= 100000:
        score += 8
        reasons.append("Strong volume")
    elif volume_24h >= 25000:
        score += 4
        reasons.append("Usable volume")
    else:
        reasons.append("Low volume risk")

    if minutes_left is not None:
        if 5 <= minutes_left <= 15:
            score += 25
            reasons.append("Ideal 15m scalp countdown window")
        elif 2 <= minutes_left < 5:
            score += 15
            reasons.append("Fast countdown volatility")
        elif 15 < minutes_left <= 45:
            score += 8
            reasons.append("Enough time for repricing")
        elif minutes_left < 2:
            score -= 20
            reasons.append("Expiration risk")
        else:
            reasons.append("Longer than ideal scalp window")

    score = max(0, min(100, score))

    if score >= 90:
        grade = "A+"
        setup = "HIGH-CONVICTION SCALP"
    elif score >= 80:
        grade = "A"
        setup = "STRONG SCALP"
    elif score >= 70:
        grade = "A-"
        setup = "TRADEABLE SCALP"
    elif score >= 60:
        grade = "B+"
        setup = "WATCHLIST SCALP"
    else:
        grade = "PASS"
        setup = "NO SCALP"

    quick_target = round(market_probability + 10, 1)
    strong_target = round(market_probability + 16, 1)
    stop = round(max(1, market_probability - 5), 1)

    return {
        "q5_score": score,
        "q5_grade": grade,
        "setup": setup,
        "side": side,
        "edge": round(edge, 1),
        "quick_target": quick_target,
        "strong_target": strong_target,
        "stop": stop,
        "expected_hold": expected_hold(minutes_left),
        "reasons": reasons,
    }


def expected_hold(minutes_left):
    if minutes_left is None:
        return "1-10 min"
    if minutes_left < 2:
        return "High risk / expiration close"
    if minutes_left <= 5:
        return "30 sec-3 min"
    if minutes_left <= 15:
        return "1-10 min"
    if minutes_left <= 45:
        return "5-20 min"
    return "Longer than ideal scalp window"


if __name__ == "__main__":
    test = q5_scalp_score(
        market_probability=49,
        bot_probability=55,
        spread=1,
        volume_24h=361775,
        move=8,
        minutes_left=8,
    )

    print(test)