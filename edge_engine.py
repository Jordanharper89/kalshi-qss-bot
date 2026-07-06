def implied_probability(price_cents):
    try:
        return float(price_cents)
    except:
        return 0


def calculate_edge(bot_probability, market_price):
    return round(bot_probability - market_price, 2)


def grade_edge(edge):

    if edge >= 15:
        return "A+", 95

    if edge >= 10:
        return "A", 88

    if edge >= 5:
        return "A-", 82

    if edge >= 3:
        return "B+", 76

    return "IGNORE", 0


def trade_decision(edge):

    if edge >= 5:
        return "TRADEABLE"

    if edge >= 3:
        return "WATCHLIST"

    return "NO TRADE"


def build_trade_rules(price):

    entry = round(price, 1)

    return {
        "entry": entry,
        "target": min(99, round(entry + 8, 1)),
        "strong_target": min(99, round(entry + 15, 1)),
        "stop": max(1, round(entry - 5, 1)),
        "chase": min(99, round(entry + 2, 1)),
    }


def analyze_market(
    bot_probability,
    market_probability
):

    edge = calculate_edge(
        bot_probability,
        market_probability
    )

    grade, score = grade_edge(edge)

    decision = trade_decision(edge)

    rules = build_trade_rules(
        market_probability
    )

    return {
        "bot_probability": bot_probability,
        "market_probability": market_probability,
        "edge": edge,
        "grade": grade,
        "score": score,
        "decision": decision,
        "rules": rules,
    }


if __name__ == "__main__":

    result = analyze_market(
        bot_probability=63,
        market_probability=52
    )

    print(result)