import time
import requests
from datetime import datetime, timezone

from config import BASE_URL
from grading import to_cents, to_float

MAX_SERIES_TO_SCAN = 12
DELAY_SECONDS = 1.5

MIN_MINUTES = 15
MAX_MINUTES = 1440

MAX_SPREAD = 6

YES_RUNNER_MIN = 8
YES_RUNNER_MAX = 35

YES_FADE_MIN = 75
YES_FADE_MAX = 92

KEYWORDS = [
    "mlb", "nfl", "nba", "nhl",
    "weather", "temp", "rain",
    "approval", "poll", "election",
    "sport", "tesla", "spacex",
    "entertainment", "movie", "song",
]

PRIORITY_KEYWORDS = [
    "mlb", "nfl", "nba", "nhl",
    "weather", "temp", "rain",
    "approval", "poll", "election",
    "sport",
]


def kalshi_url(ticker):
    return f"https://kalshi.com/markets/{str(ticker).lower()}"


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return int((close_dt - now).total_seconds() / 60)


def get_series(limit=200):
    url = f"{BASE_URL}/series"
    response = requests.get(url, params={"limit": limit}, timeout=20)
    response.raise_for_status()
    return response.json().get("series", [])


def get_series_markets(series_ticker):
    url = f"{BASE_URL}/markets"
    params = {
        "series_ticker": series_ticker,
        "status": "open",
        "limit": 100,
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json().get("markets", [])


def is_target_series(series):
    text = " ".join([
        str(series.get("ticker", "")),
        str(series.get("title", "")),
        str(series.get("category", "")),
    ]).lower()

    return any(word in text for word in KEYWORDS)


def priority_score(series):
    text = " ".join([
        str(series.get("ticker", "")),
        str(series.get("title", "")),
        str(series.get("category", "")),
    ]).lower()

    score = 0
    for i, word in enumerate(PRIORITY_KEYWORDS):
        if word in text:
            score += 100 - i

    return score


def clean_text(text):
    return str(text or "").replace("**", "").strip()


def confidence_label(score):
    if score >= 90:
        return "High"
    if score >= 80:
        return "Medium-High"
    if score >= 70:
        return "Moderate"
    return "Speculative"


def grade_from_score(score, spread):
    if score >= 90 and spread <= 3:
        return "A+"
    if score >= 80 and spread <= 5:
        return "A"
    if score >= 70 and spread <= 6:
        return "A-"
    if score >= 60 and spread <= 6:
        return "B+"
    return "PASS"


def score_runner(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = to_float(market.get("volume_24h_fp"))
    volume_total = to_float(market.get("volume_fp"))

    minutes_left = minutes_until_close(market)

    if minutes_left is None:
        return None

    if not (MIN_MINUTES <= minutes_left <= MAX_MINUTES):
        return None

    if yes_bid <= 0 or yes_ask <= 0:
        return None

    yes_spread = yes_ask - yes_bid

    if yes_spread <= 0 or yes_spread > MAX_SPREAD:
        return None

    yes_price = yes_ask
    no_price = round(100 - yes_bid, 1)
    move = abs(last - previous)

    setup = None
    side = None
    entry = None
    target = None
    stop = None
    thesis = None

    score = 0
    reasons = []

    if YES_RUNNER_MIN <= yes_price <= YES_RUNNER_MAX:
        setup = "CHEAP YES RUNNER"
        side = "BUY YES"
        entry = yes_price
        target = min(99, entry + 10)
        stop = max(1, entry - 5)
        thesis = "Buy YES low and sell into repricing if the market starts waking up."

        score += 35
        reasons.append("YES is cheap enough for runner potential")

    elif YES_FADE_MIN <= yes_price <= YES_FADE_MAX:
        no_entry = round(100 - yes_bid, 1)

        if 8 <= no_entry <= 30:
            setup = "OVERPRICED YES FADE"
            side = "BUY NO"
            entry = no_entry
            target = min(99, entry + 10)
            stop = max(1, entry - 5)
            thesis = "YES is expensive. Buy NO low and sell if YES fades."

            score += 35
            reasons.append("YES appears expensive; NO is cheap enough for fade setup")

    if setup is None:
        return None

    if yes_spread <= 3:
        score += 25
        reasons.append("Tight spread")
    elif yes_spread <= 6:
        score += 15
        reasons.append("Tradable spread")

    if volume_24h >= 100 or volume_total >= 1000:
        score += 20
        reasons.append("Usable volume")

    if move >= 2:
        score += 15
        reasons.append("Recent movement detected")

    if minutes_left <= 240:
        score += 10
        reasons.append("Fast same-day window")
    else:
        score += 5
        reasons.append("Same-day runner window")

    grade = grade_from_score(score, yes_spread)

    if grade == "PASS":
        return None

    return {
        "setup": setup,
        "side": side,
        "grade": grade,
        "score": score,
        "confidence": confidence_label(score),
        "entry": entry,
        "target": target,
        "stop": stop,
        "thesis": thesis,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "yes_spread": yes_spread,
        "no_price": no_price,
        "last": last,
        "previous": previous,
        "move": move,
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "minutes_left": minutes_left,
        "reasons": reasons,
    }


def run_q3_same_day_runners():
    series_list = get_series(limit=200)
    target_series = [s for s in series_list if is_target_series(s)]
    target_series = sorted(target_series, key=priority_score, reverse=True)
    target_series = target_series[:MAX_SERIES_TO_SCAN]

    plays = []

    for series in target_series:
        ticker = series.get("ticker")
        if not ticker:
            continue

        time.sleep(DELAY_SECONDS)

        try:
            markets = get_series_markets(ticker)
        except Exception:
            continue

        for market in markets:
            result = score_runner(market)
            if result is None:
                continue

            market_ticker = market.get("ticker")

            plays.append({
                "title": clean_text(market.get("title")),
                "ticker": market_ticker,
                "url": kalshi_url(market_ticker),
                "series": ticker,
                "series_title": series.get("title"),
                "category": series.get("category"),
                **result,
            })

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)

    print("\nQ3 SAME-DAY RUNNERS")
    print("Goal: Buy low, sell higher")
    print("Types: Cheap YES Runner | Overpriced YES Fade")
    print("Window: 15 minutes to 24 hours")
    print("-" * 60)

    if not plays:
        print("NO RUNNER")
        print("No same-day runner/fade setups right now.")
        return

    for i, play in enumerate(plays, start=1):
        print("-" * 60)
        print(f"#{i} | {play['setup']}")
        print(f"Grade: {play['grade']}")
        print(f"Score: {play['score']}/100")
        print(f"Confidence: {play['confidence']}")
        print("")
        print(f"Side: {play['side']}")
        print(f"Market: {play['title']}")
        print(f"Series: {play['series_title']}")
        print(f"Category: {play['category']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Kalshi: {play['url']}")
        print("")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"YES Bid/Ask: {play['yes_bid']}c / {play['yes_ask']}c")
        print(f"NO Approx Price: {play['no_price']}c")
        print(f"Spread: {play['yes_spread']}c")
        print("")
        print("Trade Rules:")
        print(f"- Entry: {play['entry']}c or better")
        print(f"- Target: {play['target']}c")
        print(f"- Stop: {play['stop']}c")
        print("")
        print("Runner Thesis:")
        print(f"- {play['thesis']}")
        print("")
        print("Edge Reasons:")
        for reason in play["reasons"]:
            print(f"- {reason}")


if __name__ == "__main__":
    run_q3_same_day_runners()