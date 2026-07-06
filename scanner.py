from datetime import datetime, timezone
from kalshi_api import get_all_event_markets
from grading import grade_market

def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")
    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    return int((close_dt - now).total_seconds() / 60)

def classify_scan_type(minutes_left):
    if minutes_left is None:
        return "UNKNOWN"
    if minutes_left <= 120:
        return "QSS"
    if minutes_left <= 1440:
        return "FSS"
    return "LTS"

def run_scan(mode="QSS", max_pages=10):
    markets = get_all_event_markets(max_event_pages=max_pages)
    plays = []

    for market in markets:
        minutes_left = minutes_until_close(market)
        scan_type = classify_scan_type(minutes_left)

        if scan_type != mode:
            continue

        grade_data = grade_market(market)

        if grade_data["grade"] == "PASS":
            continue

        entry = grade_data["yes_ask"]
        target = min(99, entry + 8)
        stop = max(1, entry - 5)

        plays.append({
            "title": market.get("title"),
            "ticker": market.get("ticker"),
            "scan_type": scan_type,
            "minutes_left": minutes_left,
            "entry": entry,
            "target": target,
            "stop": stop,
            **grade_data,
        })

    return sorted(plays, key=lambda x: x["score"], reverse=True)

def print_scan(mode="QSS"):
    plays = run_scan(mode=mode, max_pages=20)

    print(f"\n{mode} LIVE KALSHI SCAN")
    print("-" * 60)

    if not plays:
        print("No A-, A, or A+ opportunities found.")
        return

    for play in plays[:10]:
        print("-" * 60)
        print(f"Grade: {play['grade']} ({play['score']}/100)")
        print(f"Market: {play['title']}")
        print(f"Ticker: {play['ticker']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}¢")
        print(f"YES Bid: {play['yes_bid']}¢")
        print(f"YES Ask: {play['yes_ask']}¢")
        print(f"Spread: {play['spread']}¢")
        print(f"Liquidity: ${play['liquidity']}")
        print(f"Volume 24h: {play['volume_24h']}")
        print(f"Entry: {play['entry']}¢")
        print(f"Target Exit: {play['target']}¢")
        print(f"Stop: {play['stop']}¢")
        print("Systems:")
        for system in play["systems"]:
            print(f" - {system}")
        print("Reasons:")
        for reason in play["reasons"]:
            print(f" - {reason}")

if __name__ == "__main__":
    print_scan("QSS")