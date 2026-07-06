import requests, json

BASE = "https://external-api.kalshi.com/trade-api/v2"

for endpoint in ["/events", "/series"]:
    print("\n======================")
    print(endpoint)
    print("======================")

    try:
        r = requests.get(BASE + endpoint, params={"limit": 5}, timeout=15)
        print("status:", r.status_code)
        print(json.dumps(r.json(), indent=2)[:4000])
    except Exception as e:
        print("ERROR:", e)