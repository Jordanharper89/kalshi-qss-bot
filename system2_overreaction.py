from q1_crypto import find_crypto_events, to_cents, minutes_until_close
from kalshi_api import get_event_markets


def detect_overreaction(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    minutes_left = minutes_until_close(market)
    spread = yes_ask - yes_bid
    price = last if last > 0 else yes_ask
    move = last - previous if previous > 0 else 0

    if yes_bid <= 0 or yes_ask <= 0:
        return None

    signal = "PASS"
    reason = ""

    if abs(move) >= 20 and 1 <= minutes_left <= 15 and spread <= 4:
        signal = "OVERREACTION WATCH"
        reason = "Price moved 20c+ quickly with tight spread."

    if price >= 80 and 1 <= minutes_left <= 15:
        signal = "AVOID CHASE"
        reason = "Contract is already priced too high."

    if price <= 20 and 1 <= minutes_left <= 15:
        signal = "LOTTO ZONE"
        reason = "Contract is too cheap and likely one-sided."

    return {
        "signal": signal,
        "title": market.get("title"),
        "ticker": market.get("ticker"),
        "minutes_left": minutes_left,
        "price": price,
        "previous": previous,
        "move": move,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "spread": spread,
        "reason": reason,
    }


def run_system2():
    events = find_crypto_events()
    rows = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            row = detect_overreaction(market)

            if row is None:
                continue

            if row["signal"] != "PASS":
                row["event"] = event
                rows.append(row)

    print("\nSYSTEM 2 - OVERREACTION DETECTOR")
    print("-" * 60)

    if not rows:
        print("No overreaction signals right now.")
        return

    for row in rows[:10]:
        print("-" * 60)
        print(f"Signal: {row['signal']}")
        print(f"Market: {row['title']}")
        print(f"Event: {row['event']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Price: {row['price']}c")
        print(f"Previous: {row['previous']}c")
        print(f"Move: {row['move']}c")
        print(f"Bid/Ask: {row['yes_bid']}c / {row['yes_ask']}c")
        print(f"Spread: {row['spread']}c")
        print(f"Reason: {row['reason']}")


if __name__ == "__main__":
    run_system2()