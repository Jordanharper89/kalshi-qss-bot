from q1_crypto import find_current_events, score_market
from kalshi_api import get_event_markets

events = find_current_events()

print("\nDEBUG Q1 CRYPTO")
print("Events found:", len(events))

for event in events:
    print("\n" + "-" * 60)
    print("Event:", event)

    markets = get_event_markets(event)

    for market in markets:
        s = score_market(market)

        print("Market:", market.get("ticker"))
        print("Title:", market.get("title"))
        print("Score:", s["score"])
        print("Minutes Left:", s["minutes_left"])
        print("Price:", s["price"])
        print("Bid/Ask:", s["yes_bid"], "/", s["yes_ask"])
        print("Spread:", s["spread"])
        print("Volume 24h:", s["volume_24h"])
        print("Reasons:", s["reasons"])