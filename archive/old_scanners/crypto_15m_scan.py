from datetime import datetime, timezone
from kalshi_api import get_event_markets

EVENTS = [
    "KXBTC15M-26JUN182130",
    "KXSOL15M-26JUN182130",
]

def to_cents(value):
    try:
        return round(float(value) * 100, 1)
    except:
        return 0

def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return int((close_dt - now).total_seconds() / 60)

print("\nCRYPTO 15M TEST SCAN\n")

for event in EVENTS:
    print("-" * 60)
    print("Event:", event)

    markets = get_event_markets(event)

    for market in markets:
        print("Market:", market.get("ticker"))
        print("Title:", market.get("title"))
        print("YES Bid:", to_cents(market.get("yes_bid_dollars")), "¢")
        print("YES Ask:", to_cents(market.get("yes_ask_dollars")), "¢")
        print("Last:", to_cents(market.get("last_price_dollars")), "¢")
        print("Volume 24h:", market.get("volume_24h_fp"))
        print("Minutes Left:", minutes_until_close(market))
        print()