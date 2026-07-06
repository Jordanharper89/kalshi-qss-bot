import requests
from config import BASE_URL

tickers = [
    "KXBTC15M-26JUN182130",
    "KXBTC15M-26JUN182130-30",
    "KXSOL15M-26JUN182130",
]

for ticker in tickers:
    print("\n" + "-" * 60)
    print("Testing event:", ticker)
    url = f"{BASE_URL}/events/{ticker}"
    r = requests.get(url, timeout=20)
    print("Event status:", r.status_code)
    print(r.text[:500])

    print("Testing market:", ticker)
    url = f"{BASE_URL}/markets/{ticker}"
    r = requests.get(url, timeout=20)
    print("Market status:", r.status_code)
    print(r.text[:500])