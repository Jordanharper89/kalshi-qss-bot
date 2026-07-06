from q1_crypto import find_crypto_events
from qss_crypto import score_qss_market
from kalshi_api import get_event_markets


def run_debug():
    events = find_crypto_events()
    rows = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            s = score_qss_market(market)

            if s is None:
                continue

            rows.append({
                "event": event,
                "ticker": market.get("ticker"),
                "title": market.get("title"),
                **s
            })

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    print("\nDEBUG QSS CRYPTO BOARD")
    print("Showing top raw BTC/ETH/SOL 15m contracts")
    print("-" * 60)

    if not rows:
        print("No live rows found. Likely all bid/ask are 0.")
        return

    for row in rows[:15]:
        print("-" * 60)
        print(f"Grade: {row['grade']} | Score: {row['score']}")
        print(f"Market: {row['title']}")
        print(f"Event: {row['event']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Price: {row['price']}¢")
        print(f"Bid/Ask: {row['yes_bid']}¢ / {row['yes_ask']}¢")
        print(f"Spread: {row['spread']}¢")
        print(f"Volume 24h: {row['volume_24h']}")
        print(f"Move: {row['move']}¢")
        print("Reasons:", ", ".join(row["reasons"]) if row["reasons"] else "None")


if __name__ == "__main__":
    run_debug()