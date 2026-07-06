import requests
from config import BASE_URL

def get_orderbook(ticker, depth=10):
    url = f"{BASE_URL}/markets/{ticker}/orderbook"

    response = requests.get(
        url,
        params={"depth": depth},
        timeout=10
    )

    response.raise_for_status()
    return response.json()

def parse_orderbook(data):
    book = data.get("orderbook_fp", {})

    yes_bids = book.get("yes_dollars", [])
    no_bids = book.get("no_dollars", [])

    if not yes_bids or not no_bids:
        return None

    best_yes_bid = float(yes_bids[0][0])
    best_no_bid = float(no_bids[0][0])

    yes_bid_cents = round(best_yes_bid * 100)
    yes_ask_cents = round((1 - best_no_bid) * 100)

    spread_cents = yes_ask_cents - yes_bid_cents

    yes_depth = sum(float(level[1]) for level in yes_bids[:5])
    no_depth = sum(float(level[1]) for level in no_bids[:5])

    return {
        "yes_bid": yes_bid_cents,
        "yes_ask": yes_ask_cents,
        "mid": round((yes_bid_cents + yes_ask_cents) / 2, 1),
        "spread": spread_cents,
        "yes_depth": yes_depth,
        "no_depth": no_depth,
        "total_depth": yes_depth + no_depth,
    }

if __name__ == "__main__":
    ticker = input("Paste ticker: ").strip()
    raw = get_orderbook(ticker)
    parsed = parse_orderbook(raw)

    if parsed is None:
        print("\nPASS: Empty or unusable order book.")
    else:
        print("\nPARSED ORDER BOOK")
        print(parsed)