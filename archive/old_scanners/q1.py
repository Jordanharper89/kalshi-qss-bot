from scanner import run_scan

def run_q1():
    plays = run_scan("QSS", max_pages=1)

    # Q1 = strict best single scalp only
    clean = []

    for play in plays:
        if play["spread"] <= 3 and 40 <= play["price"] <= 65:
            clean.append(play)

    clean = sorted(clean, key=lambda x: x["score"], reverse=True)

    print("\nQ1 QUICK SCALP SCAN")
    print("Max hold: 120 minutes")
    print("-" * 60)

    if not clean:
        print("NO PLAY")
        print("No clean Q1 scalp setup found right now.")
        return

    play = clean[0]

    print(f"Grade: {play['grade']} ({play['score']}/100)")
    print(f"Market: {play['title']}")
    print(f"Ticker: {play['ticker']}")
    print(f"Minutes Left: {play['minutes_left']}")
    print(f"Price: {play['price']}¢")
    print(f"YES Bid: {play['yes_bid']}¢")
    print(f"YES Ask: {play['yes_ask']}¢")
    print(f"Spread: {play['spread']}¢")
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
    run_q1()