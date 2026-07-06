from q4_edge_engine import snapshot, detect_category, choose_side, bot_probability_for_market
from sport_router import detect_sport
from category_validator import validate_category
from edge_engine import analyze_market


MIN_ENTRY_PRICE = 8
MAX_ENTRY_PRICE = 75
MAX_SPREAD = 8


def diagnose_market(market):
    snap = snapshot(market)

    if snap["yes_bid"] <= 0 or snap["yes_ask"] <= 0:
        return {
            "passed": False,
            "reason": "Dead bid/ask",
            "details": ["YES bid or ask is missing/zero"],
        }

    if snap["spread"] <= 0:
        return {
            "passed": False,
            "reason": "Bad spread",
            "details": [f"Spread: {snap['spread']}c"],
        }

    if snap["spread"] > MAX_SPREAD:
        return {
            "passed": False,
            "reason": "Spread too wide",
            "details": [f"Spread: {snap['spread']}c", f"Max allowed: {MAX_SPREAD}c"],
        }

    title_blob = f"{market.get('title')} {market.get('ticker')} {market.get('category')} {market.get('series_title', '')}"
    category = detect_category(title_blob)
    sport = detect_sport(title_blob) if category == "sports" else None

    validation = validate_category(category, sport)

    if not validation["valid"]:
        return {
            "passed": False,
            "reason": "Category validation failed",
            "details": [
                f"Category: {category}",
                f"Sport: {sport}",
                validation["reason"],
            ],
        }

    side, market_price = choose_side(snap)

    if market_price < MIN_ENTRY_PRICE:
        return {
            "passed": False,
            "reason": "Entry too cheap / lotto zone",
            "details": [
                f"Side: {side}",
                f"Entry: {market_price}c",
                f"Minimum allowed: {MIN_ENTRY_PRICE}c",
            ],
        }

    if market_price > MAX_ENTRY_PRICE:
        return {
            "passed": False,
            "reason": "Entry too expensive",
            "details": [
                f"Side: {side}",
                f"Entry: {market_price}c",
                f"Maximum allowed: {MAX_ENTRY_PRICE}c",
            ],
        }

    prob = bot_probability_for_market(
        market=market,
        snap=snap,
        category=category,
        side=side,
        market_price=market_price,
    )

    edge = analyze_market(
        bot_probability=prob["bot_probability"],
        market_probability=market_price,
    )

    if edge["grade"] not in ["A-", "A", "A+"]:
        return {
            "passed": False,
            "reason": "Grade below A-",
            "details": [
                f"Category: {category}",
                f"Side: {side}",
                f"Bot Probability: {edge['bot_probability']}%",
                f"Market Probability: {edge['market_probability']}%",
                f"Edge: +{edge['edge']}%",
                f"Grade: {edge['grade']}",
            ] + prob.get("reasons", []),
        }

    return {
        "passed": True,
        "reason": "Passed Q4 filters",
        "details": [
            f"Category: {category}",
            f"Sport: {sport}",
            f"Side: {side}",
            f"Bot Probability: {edge['bot_probability']}%",
            f"Market Probability: {edge['market_probability']}%",
            f"Edge: +{edge['edge']}%",
            f"Grade: {edge['grade']}",
        ],
    }


if __name__ == "__main__":
    print("ticker_diagnoser loaded")