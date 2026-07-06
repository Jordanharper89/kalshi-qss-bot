from datetime import datetime, timezone
from kalshi_api import get_all_event_markets
from grading import grade_market

MIN_HOLD_MINUTES = 3
MAX_HOLD_MINUTES = 10080  # 7 days

CATEGORIES = [
    "sports",
    "entertainment",
    "science and technology",
    "technology",
]

KEYWORDS = [
    "tesla",
    "spacex",
    "starship",
    "nfl",
    "nba",
    "mlb",
    "football",
    "basketball",
    "baseball",
    "movie",
    "album",
    "song",
    "streaming",
]


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    return int((close_dt - now).total_seconds() / 60)


def is_q2_market(market):
    category = str(market.get("category", "")).lower()
    title = str(market.get("title", "")).lower()
    ticker = str(market.get("ticker", "")).lower()

    text = f"{category} {title} {ticker}"

    if category in CATEGORIES:
        return True

    if any(k in text for k in KEYWORDS):
        return True

    return False


def hold_label(minutes_left):
    if minutes_left is None:
        return "UNKNOWN"
    if minutes_left <= 120:
        return "Quick Swing"
    if minutes_left <= 1440:
        return "Same-Day Swing"
    if minutes_left <= 10080:
        return "Multi-Day Swing"
    return "Too Long"


def run_q2():
    markets = get_all_event_markets(max_event_pages=3)
    plays = []

    for market in markets:
        if not is_q2_market(market):
            continue

        minutes_left = minutes_until_close(market)

        if minutes_left is None:
            continue

        if minutes_left < MIN_HOLD_MINUTES:
            continue

        if minutes_left > MAX_HOLD_MINUTES:
            continue

        g = grade_market(market)

        if g["grade"] == "PASS":
            continue

        if g["yes_ask"] > 80:
            continue

        plays.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "category": market.get("category"),
            "minutes_left": minutes_left,
            "hold": hold_label(minutes_left),
            **g
        })

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)

    print("\nQ2 SWING SCANNER")
    print("Sports / Entertainment / Technology / Tesla / SpaceX")
    print("Hold time: 3 minutes to 7 days")
    print("-" * 60)

    if not plays:
        print("NO PLAY")
        print("No A-, A, or A+ Q2 swing setups right now.")
        return

    for i, play in enumerate(plays[:10], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']} ({play['score']}/100)")
        print(f"Market: {play['title']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Category: {play['category']}")
        print(f"Hold Type: {play['hold']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"YES Bid: {play['yes_bid']}c")
        print(f"YES Ask: {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print(f"Volume 24h: {play['volume_24h']}")
        print(f"Entry: {play['yes_ask']}c")
        print(f"Target: {min(99, play['yes_ask'] + 10)}c")
        print(f"Stop: {max(1, play['yes_ask'] - 7)}c")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_q2()