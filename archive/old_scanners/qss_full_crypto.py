from qss_crypto import score_qss_market
from system2_overreaction import detect_overreaction
from q1_crypto import find_crypto_events
from kalshi_api import get_event_markets

MAX_ENTRY_ASK = 75


def run_qss_full():
    events = find_crypto_events()
    candidates = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            qss = score_qss_market(market)

            if qss is None:
                continue

            if qss["grade"] == "PASS":
                continue

            if qss["yes_ask"] > MAX_ENTRY_ASK:
                continue

            sys2 = detect_overreaction(market)

            signal = "NORMAL"

            if sys2 and sys2["signal"] != "PASS":
                signal = sys2["signal"]

            candidates.append({
                "event": event,
                "ticker": market.get("ticker"),
                "title": market.get("title"),
                "signal": signal,
                **qss
            })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    print("\nQSS FULL CRYPTO SCAN")
    print("Systems 1 + 2 + 4")
    print("Rule: YES Ask must be <= 75c")
    print("-" * 60)

    if not candidates:
        print("NO PLAY")
        print("No A-, A, or A+ setups currently.")
        return

    for i, play in enumerate(candidates[:5], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Grade: {play['grade']}")
        print(f"Score: {play['score']}/100")
        print(f"Signal: {play['signal']}")
        print(f"Market: {play['title']}")
        print(f"Event: {play['event']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"YES Bid: {play['yes_bid']}c")
        print(f"YES Ask: {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print(f"Volume 24h: {play['volume_24h']}")
        print(f"Entry: {play['yes_ask']}c")
        print(f"Target: {min(99, play['yes_ask'] + 6)}c")
        print(f"Stop: {max(1, play['yes_ask'] - 4)}c")
        print("Systems:")
        print(" - System 1: Momentum")
        print(" - System 2: Overreaction Detector")
        print(" - System 4: Cross-Market Edge")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")


if __name__ == "__main__":
    run_qss_full()