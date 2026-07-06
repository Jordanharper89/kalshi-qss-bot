from datetime import datetime, timedelta, timezone
import requests

from config import BASE_URL
from kalshi_api import get_event_markets
from crypto_sources import get_crypto_source_check

SERIES = ["KXBTC15M", "KXETH15M", "KXSOL15M"]

MIN_PRICE = 40
MAX_PRICE = 65


def to_cents(value):
    try:
        return round(float(value) * 100, 1)
    except:
        return 0


def event_code(dt):
    return dt.strftime("%y%b%d%H%M").upper()


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return int((close_dt - now).total_seconds() / 60)


def event_exists(event_ticker):
    url = f"{BASE_URL}/events/{event_ticker}"

    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False


def find_crypto_events():
    now = datetime.now(timezone.utc)
    found = []

    for series in SERIES:
        for offset in range(-15, 181, 15):
            dt = now + timedelta(minutes=offset)
            minute = (dt.minute // 15) * 15
            dt = dt.replace(minute=minute, second=0, microsecond=0)

            ticker = f"{series}-{event_code(dt)}"

            if event_exists(ticker):
                found.append(ticker)

    return found


def symbol_from_ticker(ticker):
    ticker = str(ticker or "").upper()

    if "ETH" in ticker:
        return "ETH"
    if "SOL" in ticker:
        return "SOL"
    return "BTC"


def score_market(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = float(market.get("volume_24h_fp") or 0)
    spread = yes_ask - yes_bid
    minutes_left = minutes_until_close(market)
    price = yes_ask if yes_ask > 0 else last
    move = abs(last - previous)

    if minutes_left is None or minutes_left < 3 or minutes_left > 15:
        return None

    if not (MIN_PRICE <= price <= MAX_PRICE):
        return None

    if yes_bid <= 0 or yes_ask <= 0:
        return None

    if spread <= 0 or spread > 4:
        return None

    score = 0
    reasons = []

    score += 25
    reasons.append("Active 15-minute contract")

    score += 25
    reasons.append("Price in Q1 scalp zone")

    score += 25
    reasons.append("Tight spread")

    if volume_24h >= 10000:
        score += 15
        reasons.append("Strong 24h volume")

    if move >= 2:
        score += 10
        reasons.append("Recent movement")

    if score >= 90:
        grade = "A+"
    elif score >= 75:
        grade = "A"
    elif score >= 60:
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
        "minutes_left": minutes_left,
        "move": move,
        "reasons": reasons,
    }


def run_q1_crypto():
    events = find_crypto_events()
    candidates = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            s = score_market(market)

            if s is None:
                continue

            if s["grade"] == "PASS":
                continue

            ticker = market.get("ticker")
            symbol = symbol_from_ticker(ticker)

            candidates.append({
                "event": event,
                "ticker": ticker,
                "symbol": symbol,
                "title": market.get("title"),
                "source_check": get_crypto_source_check(symbol),
                **s
            })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    print("\nQ1 - ALL QUALIFIED CRYPTO PLAYS")
    print("Hold: 3-15 minutes")
    print("Rules: 40c-65c price, live bid/ask, tight spread")
    print("Sources: Kalshi + Coinbase/Binance check")
    print("-" * 60)

    if not candidates:
        print("NO PLAY")
        print("No qualified BTC/ETH/SOL scalp right now.")
        return

    for i, play in enumerate(candidates, start=1):
        entry = play["yes_ask"]

        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']}")
        print(f"Score: {play['score']}/100")
        print("Side: BUY YES")
        print(f"Symbol: {play['symbol']}")
        print(f"Market: {play['title']}")
        print(f"Event: {play['event']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"Last: {play['last']}c")
        print(f"Bid/Ask: {play['yes_bid']}c / {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print("Outside Source Check:")
        for line in play["source_check"]:
            print(f"- {line}")
        print("Trade Rules:")
        print(f"- Entry: {entry}c or better")
        print(f"- Target: {min(99, entry + 6)}c")
        print(f"- Strong Target: {min(99, entry + 12)}c")
        print(f"- Stop: {max(1, entry - 4)}c")
        print(f"- Max Hold: {play['minutes_left']} minutes")
        print(f"- Chase Rule: do not enter above {min(65, entry + 2)}c")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f"- {reason}")


if __name__ == "__main__":
    run_q1_crypto()