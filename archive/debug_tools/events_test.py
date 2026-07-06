import requests
from config import BASE_URL

url = f"{BASE_URL}/events"

response = requests.get(
    url,
    params={
        "limit": 50,
        "status": "open"
    },
    timeout=10
)

response.raise_for_status()

data = response.json()

print("EVENT COUNT:", len(data.get("events", [])))

for event in data.get("events", [])[:20]:
    print("-" * 50)
    print("Ticker:", event.get("ticker"))
    print("Title:", event.get("title"))