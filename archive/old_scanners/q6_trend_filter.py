def q6_trend_score(
    current_price=None,
    target_price=None,
    market_probability=None,
    move=0,
    volume_24h=0,
    minutes_left=None,
    chart_bias="unknown",
):
    score = 0
    reasons = []

    above_target = None

    if current_price is not None and target_price is not None:
        above_target = current_price >= target_price

        distance = current_price - target_price

        if above_target and distance >= 25:
            score += 30
            reasons.append("Price holding strongly above target")
        elif above_target and distance >= 5:
            score += 22
            reasons.append("Price holding above target")
        elif above_target:
            score += 15
            reasons.append("Price slightly above target")
        elif distance >= -10:
            score += 5
            reasons.append("Price near target")
        else:
            score -= 10
            reasons.append("Price below target")

    if market_probability is not None:
        if 40 <= market_probability <= 65:
            score += 15
            reasons.append("Good repricing zone")
        elif 65 < market_probability <= 85:
            score += 8
            reasons.append("Trend already pricing in")
        elif market_probability > 85:
            score -= 8
            reasons.append("Late chase risk")
        elif market_probability < 25:
            score -= 5
            reasons.append("Low confidence market zone")

    if move >= 20:
        score += 20
        reasons.append("Strong trend repricing")
    elif move >= 10:
        score += 15
        reasons.append("Trend momentum detected")
    elif move >= 5:
        score += 8
        reasons.append("Small trend move")

    if volume_24h >= 300000:
        score += 12
        reasons.append("Heavy market volume")
    elif volume_24h >= 100000:
        score += 8
        reasons.append("Strong market volume")
    elif volume_24h >= 25000:
        score += 4
        reasons.append("Usable market volume")

    if minutes_left is not None:
        if 5 <= minutes_left <= 20:
            score += 12
            reasons.append("Strong short-term trend window")
        elif 20 < minutes_left <= 60:
            score += 8
            reasons.append("Enough time for trend continuation")
        elif minutes_left < 3:
            score -= 10
            reasons.append("Expiration risk")
        else:
            reasons.append("Longer trend window")

    if chart_bias == "bullish":
        score += 15
        reasons.append("Manual chart bias: bullish")
    elif chart_bias == "bearish":
        score -= 15
        reasons.append("Manual chart bias: bearish")

    score = max(0, min(100, score))

    if score >= 90:
        grade = "A+"
        trend = "STRONG TREND"
    elif score >= 80:
        grade = "A"
        trend = "GOOD TREND"
    elif score >= 70:
        grade = "A-"
        trend = "TRADEABLE TREND"
    elif score >= 60:
        grade = "B+"
        trend = "WATCHLIST TREND"
    else:
        grade = "PASS"
        trend = "NO TREND EDGE"

    return {
        "q6_score": score,
        "q6_grade": grade,
        "trend": trend,
        "above_target": above_target,
        "reasons": reasons,
    }


if __name__ == "__main__":
    test = q6_trend_score(
        current_price=64110.14,
        target_price=64067.39,
        market_probability=42,
        move=35,
        volume_24h=521030,
        minutes_left=8,
        chart_bias="bullish",
    )

    print(test)