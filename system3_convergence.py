from q1_crypto import find_crypto_events
from qss_crypto import score_qss_market
from kalshi_api import get_event_markets


def symbol_from_ticker(ticker):
    if ticker.startswith("KXBTC"):
        return "BTC"
    if ticker.startswith("KXETH"):
        return "ETH"
    if ticker.startswith("KXSOL"):
        return "SOL"
    return "UNKNOWN"


def run_system3():
    events = find_crypto_events()
    rows = []

    for event in events:
        try:
            markets = get_event_markets(event)
        except:
            continue

        for market in markets:
            s = score_qss_market(market)

            if s is None:
                continue

            ticker = market.get("ticker", "")
            symbol = symbol_from_ticker(ticker)

            rows.append({
                "symbol": symbol,
                "event": event,
                "ticker": ticker,
                "title": market.get("title"),
                **s
            })

    active = [r for r in rows if r["minutes_left"] is not None and 1 <= r["minutes_left"] <= 15]

    print("\nSYSTEM 3 - CONVERGENCE / DIVERGENCE")
    print("-" * 60)

    if not active:
        print("No active BTC/ETH/SOL rows right now.")
        return

    active = sorted(active, key=lambda x: x["symbol"])

    for row in active:
        print("-" * 60)
        print(f"{row['symbol']} | {row['grade']} | Score {row['score']}/100")
        print(f"Price: {row['price']}c")
        print(f"Bid/Ask: {row['yes_bid']}c / {row['yes_ask']}c")
        print(f"Spread: {row['spread']}c")
        print(f"Minutes Left: {row['minutes_left']}")
        print(f"Ticker: {row['ticker']}")

    prices = {r["symbol"]: r["price"] for r in active if r["symbol"] in ["BTC", "ETH", "SOL"]}

    print("\nREAD:")
    if len(prices) < 2:
        print("Not enough symbols active to compare.")
        return

    high_symbol = max(prices, key=prices.get)
    low_symbol = min(prices, key=prices.get)
    gap = prices[high_symbol] - prices[low_symbol]

    if gap <= 10:
        print("CONVERGENCE: BTC/ETH/SOL are moving together.")
        print("This supports normal QSS scoring.")
    elif gap <= 25:
        print("MODERATE DIVERGENCE:")
        print(f"{high_symbol} is stronger than {low_symbol} by {gap}c.")
        print("Use caution. Prefer the cleaner spread and better price zone.")
    else:
        print("STRONG DIVERGENCE:")
        print(f"{high_symbol} is far stronger than {low_symbol} by {gap}c.")
        print("Possible overreaction or lagging-coin setup. Do not chase high prices.")


if __name__ == "__main__":
    run_system3()