import requests
from config import BASE_URL

def get_events(limit=100, cursor=None, status="open"):
    url = f"{BASE_URL}/events"
    params = {"limit": limit, "status": status}
    if cursor:
        params["cursor"] = cursor

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()

def get_all_events(max_pages=3):
    all_events = []
    cursor = None

    for _ in range(max_pages):
        data = get_events(limit=100, cursor=cursor)
        all_events.extend(data.get("events", []))
        cursor = data.get("cursor")
        if not cursor:
            break

    return all_events

def get_event_markets(event_ticker):
    url = f"{BASE_URL}/events/{event_ticker}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json().get("markets", [])

def get_all_event_markets(max_event_pages=1):
    events = get_all_events(max_pages=max_event_pages)
    all_markets = []

    for event in events:
        event_ticker = event.get("event_ticker")
        if not event_ticker:
            continue

        try:
            markets = get_event_markets(event_ticker)
            for market in markets:
                market["event_title"] = event.get("title")
                market["category"] = event.get("category")
                market["series_ticker"] = event.get("series_ticker")
            all_markets.extend(markets)
        except Exception as e:
            print(f"Skipping {event_ticker}: {e}")

    return all_markets

if __name__ == "__main__":
    markets = get_all_event_markets(max_event_pages=1)
    print(f"\nFetched {len(markets)} event markets\n")

    for market in markets[:20]:
        print("-" * 60)
        print("Title:", market.get("title"))
        print("Ticker:", market.get("ticker"))
        print("Category:", market.get("category"))
        print("YES Bid:", market.get("yes_bid_dollars"))
        print("YES Ask:", market.get("yes_ask_dollars"))
        print("Volume 24h:", market.get("volume_24h_fp"))
        print("Close:", market.get("close_time") or market.get("expiration_time"))