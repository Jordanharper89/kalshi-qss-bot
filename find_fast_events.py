from kalshi_api import get_all_events

keywords = [
    "bitcoin", "btc",
    "ethereum", "eth",
    "solana", "sol",
    "crypto",
    "15",
    "hour",
    "today",
    "weather",
    "temperature",
    "nba", "nfl", "mlb",
]

events = get_all_events(max_pages=20)

print("\nFAST EVENT SEARCH\n")

for event in events:
    text = " ".join([
        str(event.get("title", "")),
        str(event.get("event_ticker", "")),
        str(event.get("series_ticker", "")),
        str(event.get("category", "")),
        str(event.get("sub_title", "")),
    ]).lower()

    if any(k in text for k in keywords):
        print("-" * 60)
        print("Title:", event.get("title"))
        print("Event:", event.get("event_ticker"))
        print("Series:", event.get("series_ticker"))
        print("Category:", event.get("category"))
        print("Subtitle:", event.get("sub_title"))