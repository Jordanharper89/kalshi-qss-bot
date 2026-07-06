import sys
import time
import requests
from datetime import datetime, timezone

from config import BASE_URL
from q4_edge_engine import score_market

MAX_SERIES_TO_SCAN = 25
DELAY_SECONDS = 0.15
MAX_PLAYS_TO_SHOW = 10

KEYWORDS = [
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
    "mlb", "baseball", "nba", "basketball", "nfl", "football",
    "nhl", "hockey", "soccer", "world cup", "fifa", "tennis",
    "golf", "rugby", "lacrosse",
    "weather", "temperature", "temp", "rain", "snow", "wind",
    "trump", "election", "poll", "approval", "president",
    "song", "album", "billboard", "spotify", "movie", "box office",
    "tesla", "spacex", "starship",
]

BLOCKED_TICKER_PARTS = ["KXMVE", "MULTIGAME", "CROSSCATEGORY"]


def priority_score(series):
    text = f"{series.get('ticker','')} {series.get('title','')} {series.get('category','')}".lower()

    score = 0

    priority_words = [
        "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
        "temperature", "temp", "weather", "rain", "snow",
        "mlb", "baseball",
        "world cup", "soccer", "fifa",
        "nba", "wnba", "basketball",
    ]

    for i, word in enumerate(priority_words):
        if word in text:
            score += 100 - i

    bad_words = [
        "senate",
        "governor",
        "nominee",
        "primary",
        "parliament",
        "presidential winner",
        "election",
    ]

    for word in bad_words:
        if word in text:
            score -= 50

    return score


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")

    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    return int((close_dt - now).total_seconds() / 60)


def get_mode():
    if len(sys.argv) < 2:
        return "all"

    mode = sys.argv[1].strip().lower()

    if mode in ["all", "30m", "3h", "24h", "long"]:
        return mode

    return "all"


def hold_label(mode):
    labels = {
        "30m": "0-30 minutes",
        "3h": "30 minutes-3 hours",
        "24h": "3 hours-24 hours",
        "long": "24 hours+",
        "all": "All hold times",
    }

    return labels.get(mode, "All hold times")


def hold_filter(minutes_left, mode):
    if minutes_left is None:
        return False

    if mode == "30m":
        return 0 <= minutes_left <= 30

    if mode == "3h":
        return 30 < minutes_left <= 180

    if mode == "24h":
        return 180 < minutes_left <= 1440

    if mode == "long":
        return minutes_left > 1440

    return True


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


def is_target_series(series):
    text = f"{series.get('ticker','')} {series.get('title','')} {series.get('category','')}".lower()
    return any(word in text for word in KEYWORDS)


def is_blocked_market(market):
    text = f"{market.get('ticker','')} {market.get('title','')}".upper()
    return any(blocked in text for blocked in BLOCKED_TICKER_PARTS)


def cap_grade_for_hold(play, mode, minutes_left):
    play["grade_cap_reasons"] = []

    if mode == "long" or (minutes_left is not None and minutes_left > 1440):
        if play["grade"] in ["A+", "A", "A-"]:
            play["grade"] = "B+"
            play["score"] = min(play["score"], 76)
            play["grade_cap_reasons"].append(
                "Grade capped: long-hold market needs outside confirmation"
            )
            return None

    return play


def run_q4_series_edge(mode=None):
    mode = mode or get_mode()

    print()
    print("Q4 SERIES EDGE ENGINE")
    print("Fast Mode: real series markets only")
    print("Blocked: KXMVE / MULTIGAME / CROSSCATEGORY")
    print("Grades: A- / A / A+ Only")
    print(f"Hold Filter: {hold_label(mode)}")
    print("Long Hold Rule: capped unless outside-confirmed")
    print("Priority: crypto / weather / MLB / soccer / NBA first")
    print(f"Scan Limit: {MAX_SERIES_TO_SCAN} series")
    print("-" * 60)

    series_list = get_series()
    target_series = [s for s in series_list if is_target_series(s)]
    target_series = sorted(target_series, key=priority_score, reverse=True)
    target_series = target_series[:MAX_SERIES_TO_SCAN]

    plays = []

    print(f"Target Series Found: {len(target_series)}")
    print("-" * 60)

    for series in target_series:
        series_ticker = series.get("ticker")
        series_title = series.get("title")

        if not series_ticker:
            continue

        print(f"Checking: {series_ticker} | {series_title}")
        time.sleep(DELAY_SECONDS)

        try:
            markets = get_series_markets(series_ticker)
        except Exception as e:
            print(f"Skipping {series_ticker}: {e}")
            continue

        for market in markets:
            if is_blocked_market(market):
                continue

            minutes_left = minutes_until_close(market)

            if not hold_filter(minutes_left, mode):
                continue

            market["series_title"] = series_title

            result = score_market(market)

            if not result:
                continue

            result["series"] = series_ticker
            result["series_title"] = series_title
            result["minutes_left"] = minutes_left

            result = cap_grade_for_hold(result, mode, minutes_left)

            if result:
                plays.append(result)

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)
    plays = plays[:MAX_PLAYS_TO_SHOW]

    if not plays:
        print("-" * 60)
        print("NO EDGE FOUND")
        return

    for i, play in enumerate(plays, start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']}")
        print(f"Decision: {play['decision']}")
        print(f"Side: {play['side']}")
        print(f"Category: {play['category']}")

        if play.get("sport"):
            print(f"Sport: {play['sport']}")

        print(f"Series: {play.get('series_title')}")
        print(f"Minutes Left: {play.get('minutes_left')}")
        print(f"Bot Probability: {play['bot_probability']}%")
        print(f"Market Probability: {play['market_probability']}%")
        print(f"Edge: +{play['edge']}%")
        print()
        print(play["title"])
        print(f"Ticker: {play['ticker']}")
        print(f"Kalshi: {play['url']}")
        print()
        print("Trade Rules:")
        print(f"- Entry: {play['rules']['entry']}c")
        print(f"- Target: {play['rules']['target']}c")
        print(f"- Strong Target: {play['rules']['strong_target']}c")
        print(f"- Stop: {play['rules']['stop']}c")
        print(f"- Chase Rule: do not enter above {play['rules']['chase']}c")

        if play.get("reasons"):
            print()
            print("Reasons:")
            for reason in play["reasons"]:
                print(f"- {reason}")


if __name__ == "__main__":
    run_q4_series_edge()