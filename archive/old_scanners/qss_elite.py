from qss_crypto import score_qss_market
from system2_overreaction import detect_overreaction
from system3_convergence import symbol_from_ticker
from q1_crypto import find_crypto_events
from kalshi_api import get_event_markets

MAX_ENTRY_ASK = 75


def get_active_rows():
    events = find_crypto_events()
    rows = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            qss = score_qss_market(market)

            if qss is None:
                continue

            if qss["yes_ask"] > MAX_ENTRY_ASK:
                continue

            ticker = market.get("ticker", "")
            symbol = symbol_from_ticker(ticker)

            rows.append({
                "symbol": symbol,
                "event": event,
                "ticker": ticker,
                "title": market.get("title"),
                **qss
            })

    return rows


def system3_read(rows):
    active = [
        r for r in rows
        if r["minutes_left"] is not None and 1 <= r["minutes_left"] <= 15
    ]

    prices = {
        r["symbol"]: r["price"]
        for r in active
        if r["symbol"] in ["BTC", "ETH", "SOL"]
    }

    if len(prices) < 2:
        return "INSUFFICIENT", 0, "Not enough symbols active."

    high_symbol = max(prices, key=prices.get)
    low_symbol = min(prices, key=prices.get)
    gap = prices[high_symbol] - prices[low_symbol]

    if gap <= 10:
        return "CONVERGENCE", 10, "BTC/ETH/SOL are moving together."
    if gap <= 25:
        return "MODERATE DIVERGENCE", -5, f"{high_symbol} stronger than {low_symbol} by {gap}c."
    return "STRONG DIVERGENCE", -15, f"{high_symbol} far stronger than {low_symbol} by {gap}c."


def final_grade(score):
    if score >= 95:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 65:
        return "A-"
    return "PASS"


def run_qss_elite():
    rows = get_active_rows()
    sys3_label, sys3_bonus, sys3_reason = system3_read(rows)

    candidates = []

    for row in rows:
        if row["grade"] == "PASS":
            continue

        sys2 = detect_overreaction(row)
        signal = "NORMAL"

        if sys2 and sys2["signal"] != "PASS":
            signal = sys2["signal"]

        elite_score = row["score"] + sys3_bonus

        if signal in ["AVOID CHASE", "LOTTO ZONE"]:
            elite_score -= 20

        grade = final_grade(elite_score)

        if grade == "PASS":
            continue

        row["elite_score"] = elite_score
        row["elite_grade"] = grade
        row["system2_signal"] = signal
        row["system3_label"] = sys3_label
        row["system3_reason"] = sys3_reason

        candidates.append(row)

    candidates = sorted(candidates, key=lambda x: x["elite_score"], reverse=True)

    print("\nQSS ELITE CRYPTO SCAN")
    print("Systems 1 + 2 + 3 + 4")
    print("Rule: YES Ask must be <= 75c")
    print("-" * 60)
    print(f"System 3: {sys3_label}")
    print(f"System 3 Read: {sys3_reason}")
    print("-" * 60)

    if not candidates:
        print("NO PLAY")
        print("No elite A-, A, or A+ setups currently.")
        return

    for i, play in enumerate(candidates[:5], start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Elite Grade: {play['elite_grade']}")
        print(f"Elite Score: {play['elite_score']}/100")
        print(f"System 2 Signal: {play['system2_signal']}")
        print(f"Market: {play['title']}")
        print(f"Symbol: {play['symbol']}")
        print(f"Event: {play['event']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"YES Bid: {play['yes_bid']}c")
        print(f"YES Ask: {play['yes_ask']}c")
        print(f"Spread: {play['spread']}c")
        print(f"Entry: {play['yes_ask']}c")
        print(f"Target: {min(99, play['yes_ask'] + 6)}c")
        print(f"Stop: {max(1, play['yes_ask'] - 4)}c")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")
        print(f" - System 3: {play['system3_reason']}")


if __name__ == "__main__":
    run_qss_elite()