import requests
from config import BASE_URL

def main():
    print("INSPECTING RAW KALSHI MARKETS")
    print("-" * 60)

    r = requests.get(
        f"{BASE_URL}/markets",
        params={"status": "open", "limit": 10},
        timeout=20,
    )

    print("Status:", r.status_code)

    data = r.json()
    markets = data.get("markets", [])

    print("Markets found:", len(markets))
    print("-" * 60)

    for i, m in enumerate(markets, start=1):
        print(f"#{i}")
        print("title:", m.get("title"))
        print("ticker:", m.get("ticker"))
        print("category:", m.get("category"))
        print("yes_bid_dollars:", m.get("yes_bid_dollars"))
        print("yes_ask_dollars:", m.get("yes_ask_dollars"))
        print("last_price_dollars:", m.get("last_price_dollars"))
        print("previous_price_dollars:", m.get("previous_price_dollars"))
        print("volume_24h_fp:", m.get("volume_24h_fp"))
        print("volume_fp:", m.get("volume_fp"))
        print("raw keys:", list(m.keys())[:40])
        print("-" * 60)

if __name__ == "__main__":
    main()