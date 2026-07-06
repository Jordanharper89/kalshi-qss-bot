from kalshi_api import get_all_markets

markets = get_all_markets(max_pages=20)

counts = {}

for m in markets:
    ticker = m.get("ticker", "")

    prefix = ticker.split("-")[0]

    counts[prefix] = counts.get(prefix, 0) + 1

for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{k}: {v}")