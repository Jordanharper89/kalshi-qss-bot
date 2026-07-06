import time
import re
import requests
from datetime import datetime, timezone

from config import BASE_URL
from grading import to_cents, to_float

MAX_SERIES_TO_SCAN = 8
DELAY_SECONDS = 1.5

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

MIN_MINUTES = 15
MAX_MINUTES = 1440
MIN_PRICE = 25
MAX_PRICE = 75
MAX_ASK = 75
MAX_SPREAD = 6


def clean_text(text):
    return str(text or "").replace("**", "").strip()


def prediction_info(title):
    title = clean_text(title)

    range_match = re.search(r"(\d+)-(\d+)°", title)
    if range_match:
        low = range_match.group(1)
        high = range_match.group(2)
        thesis = f"BUY YES if it finishes at {low}° or {high}°. BUY NO if it finishes outside that range."
        return "RANGE", title, thesis

    if ">" in title:
        clean = title.replace(">", "ABOVE ")
        thesis = "BUY YES if the result finishes ABOVE that number. BUY NO if it finishes at or below that number."
        return "ABOVE", clean, thesis

    if "<" in title:
        clean = title.replace("<", "BELOW ")
        thesis = "BUY YES if the result finishes BELOW that number. BUY NO if it finishes at or above that number."
        return "BELOW", clean, thesis

    return "STANDARD", title, "BUY YES if the market statement happens. BUY NO if it does not happen."


def confidence_label(score):
    if score >= 90:
        return "High"
    if score >= 80:
        return "Medium-High"
    if score >= 70:
        return "Moderate"
    return "Low"


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
    params = {"series_ticker": series_ticker, "status": "open", "limit": 100}
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


def clean_grade(score, spread):
    natural_grade = "PASS"

    if score >= 90:
        natural_grade = "A+"
    elif score >= 80:
        natural_grade = "A"
    elif score >= 70:
        natural_grade = "A-"

    spread_grade = "PASS"

    if spread <= 3:
        spread_grade = "A+"
    elif spread <= 5:
        spread_grade = "A"
    elif spread <= 6:
        spread_grade = "A-"

    order = {"PASS": 0, "A-": 1, "A": 2, "A+": 3}

    final_grade = natural_grade
    cap_reason = ""

    if order[spread_grade] < order[natural_grade]:
        final_grade = spread_grade
        cap_reason = f"Grade capped at {spread_grade} because spread is {spread}c"

    return final_grade, cap_reason


def score_market(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = to_float(market.get("volume_24h_fp"))
    volume_total = to_float(market.get("volume_fp"))

    minutes_left = minutes_until_close(market)
    spread = yes_ask - yes_bid
    price = yes_ask if yes_ask > 0 else last
    move = abs(last - previous)

    if minutes_left is None:
        return None
    if not (MIN_MINUTES <= minutes_left <= MAX_MINUTES):
        return None
    if yes_bid <= 0 or yes_ask <= 0:
        return None
    if not (MIN_PRICE <= price <= MAX_PRICE):
        return None
    if yes_ask > MAX_ASK:
        return None
    if spread <= 0 or spread > MAX_SPREAD:
        return None

    score = 50
    reasons = ["Hard price zone passed", "Hard spread rule passed"]

    if volume_24h >= 50 or volume_total >= 1000:
        score += 20
        reasons.append("Usable volume")

    if move >= 2:
        score += 15
        reasons.append("Recent movement")

    if minutes_left <= 240:
        score += 10
        reasons.append("Fast trade window")
    else:
        score += 5
        reasons.append("Intraday swing window")

    grade, grade_cap_reason = clean_grade(score, spread)

    return {
        "grade": grade,
        "grade_cap_reason": grade_cap_reason,
        "score": score,
        "confidence": confidence_label(score),
        "price": price,
        "last": last,
        "previous": previous,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "spread": spread,
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "minutes_left": minutes_left,
        "move": move,
        "reasons": reasons,
    }


def run_q2_series():
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
            result = score_market(market)
            if result is None or result["grade"] == "PASS":
                continue

            entry = result["yes_ask"]
            title = clean_text(market.get("title"))
            pred_type, prediction, thesis = prediction_info(title)

            plays.append({
                "side": "BUY YES",
                "prediction_type": pred_type,
                "prediction": prediction,
                "trade_thesis": thesis,
                "series": ticker,
                "series_title": series.get("title"),
                "category": series.get("category"),
                "title": title,
                "ticker": market.get("ticker"),
                "entry": entry,
                "target": min(99, entry + 8),
                "stop": max(1, entry - 5),
                "chase_limit": min(MAX_ASK, entry + 2),
                **result,
            })

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)

    print("\nQ2 - ALL QUALIFIED FAST TRADES")
    print("Hold: 15 minutes to 24 hours")
    print("Rules: price 25c-75c, ask <= 75c, spread <= 6c")
    print("Grades: A+ spread <=3, A spread <=5, A- spread <=6")
    print("-" * 60)

    if not plays:
        print("NO PLAY")
        print("No qualified Q2 fast trades right now.")
        return

    for i, play in enumerate(plays, start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']}")
        print(f"Score: {play['score']}/100")
        print(f"Confidence: {play['confidence']}")
        if play["grade_cap_reason"]:
            print(f"Grade Cap: {play['grade_cap_reason']}")
        print(f"Side: {play['side']}")
        print(f"Prediction Type: {play['prediction_type']}")
        print(f"Prediction: {play['prediction']}")
        print(f"Trade Thesis: {play['trade_thesis']}")
        print(f"Market: {play['title']}")
        print(f"Series: {play['series_title']}")
        print(f"Category: {play['category']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"Last: {play['last']}c")
        print(f"Bid/Ask: {play['yes_bid']}c / {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print("Trade Rules:")
        print(f" - Entry: {play['entry']}c or better")
        print(f" - Target: {play['target']}c")
        print(f" - Stop: {play['stop']}c")
        print(f" - Chase Rule: do not enter above {play['chase_limit']}c")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_q2_series()