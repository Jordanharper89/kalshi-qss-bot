import requests
import json
from config import BASE_URL

url = f"{BASE_URL}/events"

response = requests.get(
    url,
    params={
        "limit": 1,
        "status": "open"
    },
    timeout=10
)

response.raise_for_status()
data = response.json()

print(json.dumps(data.get("events", [])[0], indent=2))