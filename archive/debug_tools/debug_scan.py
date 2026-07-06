from kalshi_api import get_all_markets
from grading import grade_market
from scanner import minutes_until_close, classify_scan_type

markets = get_all_markets(max_pages=20)

rows = []

for market in markets:
    g = grade_market(market)
    mins = minutes_until_close(market)
    scan_type = classify_scan_type(mins)

    rows.append({
        "score": g["score"],
        "grade": g["grade"],
        "scan_type": scan_type,
        "title": market.get("title"),
        "ticker": market.get("ticker"),
        "minutes_left": mins,
        "price": g["price"],
        "yes_bid": g["yes_bid"],
        "yes_ask": g["yes_ask"],
        "spread": g["spread"],
        "liquidity": g["liquidity"],
        "volume_24h": g["volume_24h"],
        "volume_total": g["volume_total"],
        "systems": g["systems"],
        "reasons": g["reasons"],
    })

rows = sorted(rows, key=lambda x: x["score"], reverse=True)

print("\nTOP RAW MARKETS BY SCORE\n")

for row in rows[:25]:
    print("-" * 70)
    print(f"Grade: {row['grade']} | Score: {row['score']} | Type: {row['scan_type']}")
    print(f"Market: {row['title']}")
    print(f"Ticker: {row['ticker']}")
    print(f"Minutes Left: {row['minutes_left']}")
    print(f"Price: {row['price']}¢")
    print(f"Bid/Ask: {row['yes_bid']}¢ / {row['yes_ask']}¢")
    print(f"Spread: {row['spread']}¢")
    print(f"Liquidity: ${row['liquidity']}")
    print(f"Volume 24h: {row['volume_24h']}")
    print(f"Volume Total: {row['volume_total']}")
    print("Systems:", ", ".join(row["systems"]) if row["systems"] else "None")
    print("Reasons:", "; ".join(row["reasons"]) if row["reasons"] else "None")