from q1_crypto import find_crypto_events, to_cents, minutes_until_close
from kalshi_api import get_event_markets


def raw_score(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = float(market.get("volume_24h_fp") or 0)
    spread = yes_ask - yes_bid
    minutes_left = minutes_until_close(market)
    price = last if last > 0 else yes_ask
    move = abs(last - previous)

    score = 0

    if minutes_left is not None and 1 <= minutes_left <= 15:
        score += 25

    if 30 <= price <= 75:
        score += 25

    if 0 < spread <= 6:
        score += 25

    if volume_24h >= 10000:
        score += 15

    if move >= 2:
        score += 10

    return {
        "score": score,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last": last,
        "previous": previous,
        "price": price,
        "spread": spread,
        "volume_24h": volume_24h,
        "minutes_left": minutes_left,
        "move": move,
    }


def rejection_reasons(row):
    reasons = []

    if row["minutes_left"] is None:
        reasons.append("No close time")
    elif row["minutes_left"] < 1:
        reasons.append("Expired / settlement zone")
    elif row["minutes_left"] > 15:
        reasons.append("Too early")

    if row["price"] < 30:
        reasons.append("Price too low / lotto zone")
    elif row["price"] > 75:
        reasons.append("Price too high / chase zone")

    if row["yes_ask"] > 75:
        reasons.append("Entry ask above 75c")

    if row["spread"] <= 0:
        reasons.append("No usable spread")
    elif row["spread"] > 6:
        reasons.append("Spread too wide")

    if row["yes_bid"] <= 0 or row["yes_ask"] <= 0:
        reasons.append("Dead bid/ask")

    if row["score"] < 60:
        reasons.append("Score below A- threshold")

    if not reasons:
        reasons.append("Close to qualifying")

    return reasons


def run_near_miss():
    events = find_crypto_events()
    rows = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            s = raw_score(market)

            if s["yes_bid"] <= 0 or s["yes_ask"] <= 0:
                continue

            if s["minutes_left"] is None:
                continue

            if s["minutes_left"] > 30:
                continue

            rows.append({
                "event": event,
                "ticker": market.get("ticker"),
                "title": market.get("title"),
                **s
            })

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    print("\nNEAR MISS BOARD")
    print("Best rejected LIVE BTC/ETH/SOL 15m setups")
    print("-" * 60)

    if not rows:
        print("No live near-miss rows found.")
        return

    for i, row in enumerate(rows[:10], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Score: {row['score']}/100")
        print(f"Market: {row['title']}")
        print(f"Event: {row['event']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Price: {row['price']}c")
        print(f"Bid/Ask: {row['yes_bid']}c / {row['yes_ask']}c")
        print(f"Spread: {row['spread']}c")
        print(f"Volume 24h: {row['volume_24h']}")
        print("Rejected because:")
        for reason in rejection_reasons(row):
            print(f" - {reason}")


if __name__ == "__main__":
    run_near_miss()