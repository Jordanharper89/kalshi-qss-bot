from kalshi_api import get_all_events

KEYWORDS = [
    "kxbtc",
    "kxeth",
    "kxsol",
    "bitcoin",
    "ethereum",
    "solana",
    "crypto",
]

events = get_all_events(max_pages=10)

print("\nCRYPTO EVENT SEARCH\n")

found = 0

for event in events:
    text = " ".join([
        str(event.get("title", "")),
        str(event.get("event_ticker", "")),
        str(event.get("series_ticker", "")),
        str(event.get("category", "")),
        str(event.get("sub_title", "")),
    ]).lower()

    if any(k in text for k in KEYWORDS):
        found += 1
        print("-" * 60)
        print("Title:", event.get("title"))
        print("Event:", event.get("event_ticker"))
        print("Series:", event.get("series_ticker"))
        print("Category:", event.get("category"))
        print("Subtitle:", event.get("sub_title"))

print("\nFound:", found)