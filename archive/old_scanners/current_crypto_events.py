from datetime import datetime, timedelta, timezone
import requests
from config import BASE_URL

SERIES = ["KXBTC15M", "KXSOL15M", "KXETH15M"]

def event_code(dt):
    # Kalshi format example: 26JUN182130
    return dt.strftime("%y%b%d%H%M").upper()

def test_event(event_ticker):
    url = f"{BASE_URL}/events/{event_ticker}"
    try:
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except:
        return False

now = datetime.now(timezone.utc)

print("\nCURRENT CRYPTO 15M EVENT FINDER\n")

found = []

for series in SERIES:
    print("-" * 60)
    print("Searching:", series)

    for offset in range(-60, 121, 15):
        dt = now + timedelta(minutes=offset)

        # round to nearest 15 minute mark
        minute = (dt.minute // 15) * 15
        dt = dt.replace(minute=minute, second=0, microsecond=0)

        ticker = f"{series}-{event_code(dt)}"

        if test_event(ticker):
            found.append(ticker)
            print("FOUND:", ticker)

print("\nFOUND EVENTS:")
for x in found:
    print(x)