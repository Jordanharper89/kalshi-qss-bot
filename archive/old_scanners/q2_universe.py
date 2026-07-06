from datetime import datetime, timezone
from kalshi_api import get_all_event_markets
from grading import to_cents, to_float

MIN_HOLD_MINUTES = 15
MAX_HOLD_MINUTES = 1440  # 24 hours

MIN_PRICE = 25
MAX_PRICE = 75
MAX_ASK = 75
MAX_SPREAD = 6


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return int((close_dt - now).total_seconds() / 60)


def hold_label(minutes_left):
    if minutes_left <= 60:
        return "Fast Scalp"
    if minutes_left <= 240:
        return "Short Trade"
    return "Intraday Swing"


def score_market_q2(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = to_float(market.get("volume_24h_fp"))
    volume_total = to_float(market.get("volume_fp"))

    minutes_left = minutes_until_close(market)
    spread = yes_ask - yes_bid
    price = last if last > 0 else yes_ask
    move = abs(last - previous)

    if minutes_left is None:
        return None

    if minutes_left < MIN_HOLD_MINUTES or minutes_left > MAX_HOLD_MINUTES:
        return None

    if yes_bid <= 0 or yes_ask <= 0:
        return None

    if yes_ask > MAX_ASK:
        return None

    score = 0
    reasons = []

    if MIN_PRICE <= price <= MAX_PRICE:
        score += 25
        reasons.append("Tradable price zone")

    if 0 < spread <= MAX_SPREAD:
        score += 25
        reasons.append("Tradable spread")

    if volume_24h >= 100 or volume_total >= 2500:
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

    if score >= 90 and spread <= 3 and volume_24h >= 100:
        grade = "A+"
    elif score >= 75 and spread <= 5:
        grade = "A"
    elif score >= 60 and spread <= 6:
        grade = "A-"
    else:
        grade = "PASS"

    return {
        "grade": grade,
        "score": score,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last": last,
        "previous": previous,
        "price": price,
        "spread": spread,
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "minutes_left": minutes_left,
        "move": move,
        "reasons": reasons,
    }


def max_hold_text(minutes_left):
    if minutes_left <= 60:
        return f"{minutes_left} minutes max"
    hours = round(minutes_left / 60, 1)
    return f"{hours} hours max"


def run_q2_universe():
    markets = get_all_event_markets(max_event_pages=5)
    plays = []

    for market in markets:
        s = score_market_q2(market)

        if s is None:
            continue

        if s["grade"] == "PASS":
            continue

        entry = s["yes_ask"]
        target = min(99, entry + 8)
        stop = max(1, entry - 5)
        chase_limit = min(MAX_ASK, entry + 2)

        plays.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "category": market.get("category"),
            "event_title": market.get("event_title"),
            "hold": hold_label(s["minutes_left"]),
            "entry": entry,
            "target": target,
            "stop": stop,
            "chase_limit": chase_limit,
            **s
        })

    plays = sorted(plays, key=lambda x: x["score"], reverse=True)

    print("\nQ2 UNIVERSE SCANNER")
    print("All Kalshi categories")
    print("Hold: 15 minutes to 24 hours")
    print("Rules: 25c-75c price, ask <= 75c, spread <= 6c")
    print("-" * 60)

    if not plays:
        print("NO PLAY")
        print("No A-, A, or A+ Q2 universe setups right now.")
        return

    for i, play in enumerate(plays[:15], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']} ({play['score']}/100)")
        print(f"Market: {play['title']}")
        print(f"Category: {play['category']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Hold Type: {play['hold']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"YES Bid: {play['yes_bid']}c")
        print(f"YES Ask: {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print(f"Volume 24h: {play['volume_24h']}")
        print(f"Volume Total: {play['volume_total']}")

        print("Trade Rules:")
        print(f" - Entry: {play['entry']}c or better")
        print(f" - Target: {play['target']}c")
        print(f" - Stop: {play['stop']}c")
        print(f" - Max Hold: {max_hold_text(play['minutes_left'])}")
        print(f" - Chase Rule: Do not enter above {play['chase_limit']}c")
        print(" - Exit Rule: take profit at target or cut at stop")
        print(" - No Re-entry Rule: do not re-enter after stop unless it appears again on a fresh scan")

        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_q2_universe()