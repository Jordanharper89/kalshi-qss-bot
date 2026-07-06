def clamp(value, low=0, high=100):
    return max(low, min(high, round(value, 1)))


def final_grade(score):
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "A-"
    if score >= 60:
        return "B+"
    return "PASS"


def final_trade_decision(
    q4_grade="PASS",
    q4_edge=0,
    q5_score=0,
    q5_grade="PASS",
    q6_score=0,
    q6_grade="PASS",
    market_probability=0,
    minutes_left=None,
):
    settlement_score = 0

    if q4_grade == "A+":
        settlement_score = 90
    elif q4_grade == "A":
        settlement_score = 82
    elif q4_grade == "A-":
        settlement_score = 74
    elif q4_grade == "B+":
        settlement_score = 64
    else:
        settlement_score = 45

    settlement_score += min(q4_edge, 20) * 0.5
    settlement_score = clamp(settlement_score)

    scalp_score = q5_score

    if q6_score >= 80:
        scalp_score += 6
    elif q6_score >= 70:
        scalp_score += 3

    if minutes_left is not None:
        if 5 <= minutes_left <= 20:
            scalp_score += 5
        elif minutes_left <= 2:
            scalp_score -= 12

    scalp_score = clamp(scalp_score)

    combined_score = clamp((settlement_score * 0.45) + (scalp_score * 0.45) + (q6_score * 0.10))

    if q5_grade in ["A+", "A", "A-"] and scalp_score >= settlement_score:
        lean = "LEAN SCALP"
        strategy = "Quick repricing trade"
    elif q4_grade in ["A+", "A", "A-"]:
        lean = "LEAN SETTLEMENT"
        strategy = "Hold to maturity / settlement edge"
    else:
        lean = "PASS"
        strategy = "No clean edge"

    if market_probability >= 80 and lean == "LEAN SCALP":
        lean = "SCALP ONLY - CHASE RISK"
        strategy = "Only scalp if already entered lower"

    return {
        "final_grade": final_grade(combined_score),
        "confidence": combined_score,
        "lean": lean,
        "strategy": strategy,
        "settlement_score": settlement_score,
        "scalp_score": scalp_score,
        "trend_score": q6_score,
    }


if __name__ == "__main__":
    print(final_trade_decision(
        q4_grade="A-",
        q4_edge=6,
        q5_score=77,
        q5_grade="A-",
        q6_score=68,
        market_probability=60,
        minutes_left=44,
    ))