from q2_universe import score_market_q2, minutes_until_close, hold_label
from kalshi_api import get_all_event_markets


def raw_reasons(market, score):
    reasons = []

    if score is None:
        reasons.append("Outside Q2 rules or dead market")
        return reasons

    if score["minutes_left"] < 15:
        reasons.append("Too close to expiration")
    elif score["minutes_left"] > 1440:
        reasons.append("Too far out")

    if score["price"] < 25:
        reasons.append("Price too low / lotto zone")
    elif score["price"] > 75:
        reasons.append("Price too high / chase zone")

    if score["yes_ask"] > 75:
        reasons.append("Ask above 75c")

    if score["spread"] > 6:
        reasons.append("Spread too wide")

    if score["score"] < 60:
        reasons.append("Score below A- threshold")

    if not reasons:
        reasons.append("Close to qualifying")

    return reasons


def run_q2_near_miss():
    markets = get_all_event_markets(max_event_pages=15)
    rows = []

    for market in markets:
        s = score_market_q2(market)

        if s is None:
            continue

        rows.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "category": market.get("category"),
            "hold": hold_label(s["minutes_left"]),
            **s
        })

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    print("\nQ2 NEAR MISS BOARD")
    print("Best rejected 15m-24h Kalshi setups")
    print("-" * 60)

    if not rows:
        print("No Q2 near-miss rows found.")
        return

    for i, row in enumerate(rows[:15], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {row['grade']}")
        print(f"Score: {row['score']}/100")
        print(f"Market: {row['title']}")
        print(f"Category: {row['category']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Hold Type: {row['hold']}")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Price: {row['price']}c")
        print(f"Bid/Ask: {row['yes_bid']}c / {row['yes_ask']}c")
        print(f"Spread: {row['spread']}c")
        print(f"Volume 24h: {row['volume_24h']}")
        print("Rejected because:")
        for reason in raw_reasons(row, row):
            print(f" - {reason}")


if __name__ == "__main__":
    run_q2_near_miss()