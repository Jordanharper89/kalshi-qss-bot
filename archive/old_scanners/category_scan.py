import sys
import requests
from datetime import datetime, timezone

from config import BASE_URL
from q4_edge_engine import score_market


MAX_SERIES_TO_SCAN = 60
MAX_PLAYS_TO_SHOW = 10


CATEGORY_KEYWORDS = {
    "bitcoin": ["btc", "bitcoin", "kxbtc", "kxbtcd"],
    "btc": ["btc", "bitcoin", "kxbtc", "kxbtcd"],
    "ethereum": ["eth", "ethereum", "kxeth"],
    "eth": ["eth", "ethereum", "kxeth"],
    "solana": ["sol", "solana", "kxsol"],
    "sol": ["sol", "solana", "kxsol"],
    "weather": ["weather", "temperature", "temp", "rain", "snow", "wind", "high", "low"],
    "mlb": ["mlb", "baseball", "pro baseball"],
    "soccer": ["soccer", "world cup", "fifa"],
}


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return int((close_dt - now).total_seconds() / 60)


def get_series(limit=500):
    r = requests.get(
        f"{BASE_URL}/series",
        params={"limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("series", [])


def get_series_markets(series_ticker):
    r = requests.get(
        f"{BASE_URL}/markets",
        params={
            "series_ticker": series_ticker,
            "status": "open",
            "limit": 100,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("markets", [])


def matches_series(series, category):
    keywords = CATEGORY_KEYWORDS.get(category, [])
    text = f"{series.get('ticker','')} {series.get('title','')} {series.get('category','')}".lower()
    return any(word in text for word in keywords)


def play_matches_category(play, category):
    ticker = str(play.get("ticker", "")).lower()
    title = str(play.get("title", "")).lower()
    series = str(play.get("series_title", "")).lower()
    detected = str(play.get("category", "")).lower()
    sport = str(play.get("sport", "")).lower()

    text = f"{ticker} {title} {series}"

    if category in ["bitcoin", "btc"]:
        return "btc" in text or "bitcoin" in text or "kxbtc" in ticker or "kxbtcd" in ticker

    if category in ["ethereum", "eth"]:
        return "eth" in text or "ethereum" in text or "kxeth" in ticker

    if category in ["solana", "sol"]:
        return "sol" in text or "solana" in text or "kxsol" in ticker

    if category == "weather":
        return detected == "weather"

    if category == "mlb":
        return detected == "sports" and sport == "mlb"

    if category == "soccer":
        return detected == "sports" and sport == "soccer"

    return False


def run_category_scan(category):
    category = str(category or "").lower().strip()

    if category not in CATEGORY_KEYWORDS:
        print("UNKNOWN CATEGORY")
        print("Use: bitcoin, solana, ethereum, weather, mlb, soccer")
        return

    print()
    print(f"{category.upper()} TOP PLAYS")
    print("Category-clean scan")
    print("Top 10 only")
    print("-" * 60)

    series_list = get_series()
    target_series = [s for s in series_list if matches_series(s, category)]
    target_series = target_series[:MAX_SERIES_TO_SCAN]

    plays = []

    for series in target_series:
        series_ticker = series.get("ticker")
        series_title = series.get("title")

        if not series_ticker:
            continue

        try:
            markets = get_series_markets(series_ticker)
        except Exception:
            continue

        for market in markets:
            minutes_left = minutes_until_close(market)

            if minutes_left is None or minutes_left <= 0:
                continue

            market["series_title"] = series_title

            result = score_market(market)

            if not result:
                continue

            result["series_title"] = series_title
            result["minutes_left"] = minutes_left

            if not play_matches_category(result, category):
                continue

            plays.append(result)

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)
    plays = plays[:MAX_PLAYS_TO_SHOW]

    if not plays:
        print("NO QUALIFIED PLAYS FOUND")
        return

    for i, play in enumerate(plays, start=1):
        print("-" * 60)
        print(f"#{i}")
        print("Grade:", play["grade"])
        print("Decision:", play["decision"])
        print("Side:", play["side"])
        print("Category:", play["category"])

        if play.get("sport"):
            print("Sport:", play["sport"])

        print("Series:", play.get("series_title"))
        print("Minutes Left:", play.get("minutes_left"))
        print("Bot Probability:", str(play["bot_probability"]) + "%")
        print("Market Probability:", str(play["market_probability"]) + "%")
        print("Edge: +" + str(play["edge"]) + "%")
        print()
        print(play["title"])
        print("Ticker:", play["ticker"])
        print("Kalshi:", play["url"])
        print()
        print("Trade Rules:")
        print("- Entry:", str(play["rules"]["entry"]) + "c")
        print("- Target:", str(play["rules"]["target"]) + "c")
        print("- Strong Target:", str(play["rules"]["strong_target"]) + "c")
        print("- Stop:", str(play["rules"]["stop"]) + "c")
        print("- Chase Rule: do not enter above", str(play["rules"]["chase"]) + "c")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python category_scan.py bitcoin")
    else:
        run_category_scan(sys.argv[1])