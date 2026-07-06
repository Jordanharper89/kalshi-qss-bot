import requests
from config import BASE_URL

KEYWORDS = [
    "sport",
    "nfl",
    "nba",
    "mlb",
    "weather",
    "rain",
    "temperature",
    "tesla",
    "spacex",
    "election",
    "politics",
    "entertainment",
    "movie",
]

url = f"{BASE_URL}/series"

params = {
    "limit": 200,
}

print("\nSERIES PROBE\n")

try:
    r = requests.get(url, params=params, timeout=20)
    print("Status:", r.status_code)
    data = r.json()

    series_list = data.get("series", [])

    found = 0

    for s in series_list:
        text = " ".join([
            str(s.get("ticker", "")),
            str(s.get("title", "")),
            str(s.get("category", "")),
        ]).lower()

        if any(k in text for k in KEYWORDS):
            found += 1
            print("-" * 60)
            print("Ticker:", s.get("ticker"))
            print("Title:", s.get("title"))
            print("Category:", s.get("category"))

    print("\nFound:", found)

except Exception as e:
    print("Error:", e)