def kalshi_url(ticker):
    return f"https://kalshi.com/markets/{str(ticker).lower()}"


def confidence_label(score):
    if score >= 90:
        return "High"
    if score >= 80:
        return "Medium-High"
    if score >= 70:
        return "Moderate"
    return "Speculative"


def grade_from_score(score):
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 80:
        return "A-"
    if score >= 75:
        return "B+"
    return "IGNORE"


def scalp_targets(entry, setup_type="standard"):
    if setup_type == "runner":
        return {
            "target": min(99, entry + 10),
            "strong_target": min(99, entry + 18),
            "stop": max(1, entry - 5),
        }

    if setup_type == "fade":
        return {
            "target": min(99, entry + 10),
            "strong_target": min(99, entry + 20),
            "stop": max(1, entry - 5),
        }

    return {
        "target": min(99, entry + 8),
        "strong_target": min(99, entry + 15),
        "stop": max(1, entry - 5),
    }


def universal_edge_score(
    price,
    spread,
    volume_24h,
    volume_total,
    move,
    minutes_left,
    setup_type="standard",
):
    score = 0
    reasons = []

    if 8 <= price <= 35 and setup_type == "runner":
        score += 25
        reasons.append("Cheap runner price zone")

    elif 25 <= price <= 75:
        score += 25
        reasons.append("Tradable price zone")

    elif 8 <= price <= 30 and setup_type == "fade":
        score += 25
        reasons.append("Cheap fade entry zone")

    if 0 < spread <= 3:
        score += 25
        reasons.append("Tight spread")
    elif 3 < spread <= 6:
        score += 15
        reasons.append("Tradable spread")

    if volume_24h >= 100 or volume_total >= 1000:
        score += 20
        reasons.append("Usable volume")

    if move >= 2:
        score += 15
        reasons.append("Recent movement / repricing")

    if minutes_left is not None:
        if minutes_left <= 240:
            score += 10
            reasons.append("Fast trade window")
        elif minutes_left <= 1440:
            score += 5
            reasons.append("Same-day trade window")

    grade = grade_from_score(score)

    return {
        "edge_score": score,
        "edge_grade": grade,
        "confidence": confidence_label(score),
        "edge_reasons": reasons,
    }


def build_trade_card(
    title,
    ticker,
    side,
    entry,
    setup_type,
    price,
    spread,
    volume_24h,
    volume_total,
    move,
    minutes_left,
    extra_reasons=None,
):
    edge = universal_edge_score(
        price=price,
        spread=spread,
        volume_24h=volume_24h,
        volume_total=volume_total,
        move=move,
        minutes_left=minutes_left,
        setup_type=setup_type,
    )

    targets = scalp_targets(entry, setup_type)

    reasons = edge["edge_reasons"][:]
    if extra_reasons:
        reasons.extend(extra_reasons)

    return {
        "title": title,
        "ticker": ticker,
        "side": side,
        "setup_type": setup_type,
        "grade": edge["edge_grade"],
        "score": edge["edge_score"],
        "confidence": edge["confidence"],
        "entry": entry,
        "target": targets["target"],
        "strong_target": targets["strong_target"],
        "stop": targets["stop"],
        "kalshi_url": kalshi_url(ticker),
        "reasons": reasons,
    }


def print_trade_card(card):
    print(f"Grade: {card['grade']}")
    print(f"Score: {card['score']}/100")
    print(f"Confidence: {card['confidence']}")
    print(f"Side: {card['side']}")
    print(f"Setup: {card['setup_type'].upper()}")
    print(f"Market: {card['title']}")
    print(f"Ticker: {card['ticker']}")
    print("Trade Rules:")
    print(f" - Entry: {card['entry']}c or better")
    print(f" - Target: {card['target']}c")
    print(f" - Strong Target: {card['strong_target']}c")
    print(f" - Stop: {card['stop']}c")
    print(f" - Kalshi URL: {card['kalshi_url']}")
    print("Edge Reasons:")
    for reason in card["reasons"]:
        print(f" - {reason}")