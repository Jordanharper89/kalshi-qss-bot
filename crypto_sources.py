import requests


def get_coinbase_price(symbol):
    pair = f"{symbol.upper()}-USD"
    url = f"https://api.coinbase.com/v2/prices/{pair}/spot"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return float(data["data"]["amount"])
    except Exception:
        return None


def get_binance_price(symbol):
    pair = f"{symbol.upper()}USDT"
    url = "https://api.binance.com/api/v3/ticker/price"

    try:
        r = requests.get(url, params={"symbol": pair}, timeout=10)
        data = r.json()
        return float(data["price"])
    except Exception:
        return None


def get_crypto_source_check(symbol):
    coinbase = get_coinbase_price(symbol)
    binance = get_binance_price(symbol)

    checks = []

    if coinbase:
        checks.append(f"Coinbase {symbol.upper()}: ${coinbase:,.2f}")

    if binance:
        checks.append(f"Binance {symbol.upper()}: ${binance:,.2f}")

    if coinbase and binance:
        diff = abs(coinbase - binance)
        avg = (coinbase + binance) / 2
        diff_pct = (diff / avg) * 100 if avg else 0

        if diff_pct <= 0.25:
            checks.append("Source Check: Coinbase/Binance aligned")
        else:
            checks.append(f"Source Check: price gap {diff_pct:.2f}%")

    if not checks:
        checks.append("Source Check: unavailable")

    return checks


if __name__ == "__main__":
    for symbol in ["BTC", "ETH", "SOL"]:
        print("-" * 60)
        print(symbol)
        for line in get_crypto_source_check(symbol):
            print(line)