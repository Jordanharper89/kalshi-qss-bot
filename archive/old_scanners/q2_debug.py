from q2_scanner import is_q2_market, minutes_until_close, hold_label
from kalshi_api import get_all_event_markets
from grading import grade_market


def run_q2_debug():
    markets = get_all_event_markets(max_event_pages=3)
    rows = []

    for market in markets:
        if not is_q2_market(market):
            continue

        mins = minutes_until_close(market)
        if mins is None:
            continue

        g = grade_market(market)

        rows.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "category": market.get("category"),
            "minutes_left": mins,
            "hold": hold_label(mins),
            **g
        })

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    print("\nQ2 DEBUG BOARD")
    print("Best raw Sports / Entertainment / Tech / Tesla / SpaceX markets")
    print("-" * 60)

    if not rows:
        print("No Q2 rows found.")
        return

    for i, row in enumerate(rows[:15], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {row['grade']}")
        print(f"Score: {row['score']}/100")
        print(f"Market: {row['title']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Category: {row['category']}")
        print(f"Hold Type: {row['hold']}")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Price: {row['price']}c")
        print(f"YES Bid: {row['yes_bid']}c")
        print(f"YES Ask: {row['yes_ask']}c")
        print(f"Spread: {row['spread']}c")
        print(f"Volume 24h: {row['volume_24h']}")
        print("Reasons:")
        for reason in row["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_q2_debug()