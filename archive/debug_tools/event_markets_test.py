import requests
import json
from config import BASE_URL

event_ticker = input("Paste event_ticker: ").strip()

url = f"{BASE_URL}/events/{event_ticker}"

response = requests.get(url, timeout=10)
response.raise_for_status()

data = response.json()

print(json.dumps(data, indent=2))