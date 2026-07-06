import requests
import json
from config import BASE_URL

tickers = [
    "KXBTC15M",
    "KXSOL15M",
    "KXETH15M",
]

for ticker in tickers:
    print("\n" + "-" * 60)
    print("Testing:", ticker)

    url = f"{BASE_URL}/events/{ticker}"

    try:
        response = requests.get(url, timeout=20)
        print("Status:", response.status_code)
        print(response.text[:1000])
    except Exception as e:
        print("Error:", e)