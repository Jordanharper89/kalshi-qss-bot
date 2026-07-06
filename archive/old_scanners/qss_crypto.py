from q1_crypto import find_crypto_events, to_cents, minutes_until_close
from kalshi_api import get_event_markets


def score_qss_market(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    volume_24h = float(market.get("volume_24h_fp") or 0)
    spread = yes_ask - yes_bid
    minutes_left = minutes_until_close(market)
    price = last if last > 0 else yes_ask
    move = abs(last - previous)

    if yes_bid <= 0 or yes_ask <= 0:
        return None

    score = 0
    reasons = []

    if minutes_left is not None and 1 <= minutes_left <= 15:
        score += 25
        reasons.append("Active 15-minute contract")

    if 30 <= price <= 75:
        score += 25
        reasons.append("Price in QSS scalp zone")

    if 0 < spread <= 6:
        score += 25
        reasons.append("Tradable spread")

    if volume_24h >= 10000:
        score += 15
        reasons.append("Strong 24h volume")

    if move >= 2:
        score += 10
        reasons.append("Recent movement")

    if score >= 90 and 40 <= price <= 65 and spread <= 3:
        grade = "A+"
    elif score >= 75 and 35 <= price <= 70 and spread <= 5:
        grade = "A"
    elif score >= 60 and 30 <= price <= 75 and spread <= 6:
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


def run_qss_crypto():
    events = find_crypto_events()
    candidates = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            s = score_qss_market(market)

            if s is None:
                continue

            if s["grade"] == "PASS":
                continue

            candidates.append({
                "event": event,
                "ticker": market.get("ticker"),
                "title": market.get("title"),
                **s
            })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    print("\nQSS CRYPTO SCALP SCAN")
    print("Top 5 BTC/ETH/SOL 15-minute scalps")
    print("-" * 60)

    if not candidates:
        print("NO PLAY")
        print("No A-, A, or A+ crypto scalps right now.")
        return

    for i, play in enumerate(candidates[:5], start=1):
        print("-" * 60)
        print(f"#{i} — {play['grade']} — Score {play['score']}/100")
        print(f"Market: {play['title']}")
        print(f"Event: {play['event']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}¢")
        print(f"YES Bid: {play['yes_bid']}¢")
        print(f"YES Ask: {play['yes_ask']}¢")
        print(f"Spread: {play['spread']}¢")
        print(f"Volume 24h: {play['volume_24h']}")
        print(f"Entry: {play['yes_ask']}¢")
        print(f"Target Exit: {min(99, play['yes_ask'] + 6)}¢")
        print(f"Stop: {max(1, play['yes_ask'] - 4)}¢")
        print("Systems:")
        print(" - System 1: Momentum")
        print(" - System 4: Cross-Market Edge")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_qss_crypto()