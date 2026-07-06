from q4_edge_engine import get_open_markets, score_market, snapshot, detect_category, choose_side, bot_probability_for_market
from edge_engine import analyze_market


MAX_RESULTS = 20


def run_q4_debug():
    print()
    print("Q4 DEBUG BOARD")
    print("Shows A+, A, A-, B+, and near misses")
    print("-" * 60)

    markets = get_open_markets()
    rows = []

    for market in markets:
        snap = snapshot(market)

        if snap["yes_bid"] <= 0 or snap["yes_ask"] <= 0:
            continue

        if snap["spread"] <= 0 or snap["spread"] > 10:
            continue

        title_blob = f"{market.get('title')} {market.get('ticker')} {market.get('category')}"
        category = detect_category(title_blob)
        side, market_price = choose_side(snap)

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

        rows.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "category": category,
            "side": side,
            "grade": edge["grade"],
            "score": edge["score"],
            "decision": edge["decision"],
            "bot_probability": edge["bot_probability"],
            "market_probability": edge["market_probability"],
            "edge": edge["edge"],
            "spread": snap["spread"],
            "move": snap["move"],
            "volume_24h": snap["volume_24h"],
            "reasons": prob["reasons"],
            "component_scores": prob["component_scores"],
        })

    rows = sorted(rows, key=lambda x: x["edge"], reverse=True)[:MAX_RESULTS]

    if not rows:
        print("No debug rows found.")
        return

    for i, row in enumerate(rows, start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {row['grade']}")
        print(f"Decision: {row['decision']}")
        print(f"Side: {row['side']}")
        print(f"Category: {row['category']}")
        print(f"Bot Probability: {row['bot_probability']}%")
        print(f"Market Probability: {row['market_probability']}%")
        print(f"Edge: +{row['edge']}%")
        print(f"Spread: {row['spread']}c")
        print(f"Move: {row['move']}c")
        print(f"Volume 24h: {row['volume_24h']}")
        print(f"Market: {row['title']}")
        print(f"Ticker: {row['ticker']}")
        print("Reasons:")
        for reason in row["reasons"]:
            print(f"- {reason}")
        if row["component_scores"]:
            print("Component Scores:")
            for key, value in row["component_scores"].items():
                print(f"- {key}: {value}")


if __name__ == "__main__":
    run_q4_debug()