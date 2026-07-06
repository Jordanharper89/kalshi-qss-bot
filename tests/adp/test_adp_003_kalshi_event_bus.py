from qseries_v2.adapters.kalshi_event_bus import kalshi_event_bus
from qseries_v2.core.event_bus import event_bus

events = []

def listener(payload):
    events.append(payload)

event_bus.subscribe("adapter.kalshi.market", listener)

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Event Bus Test",
    "yes_price": 68,
    "volume": 1000,
}

payload = kalshi_event_bus.publish_market(raw)

assert len(events) == 1
assert payload["ticker"] == "TEST-KALSHI"
assert payload["market"].source == "kalshi"
assert payload["evidence"]["category"] == "market"

print("[PASS] ADP-003 Kalshi Event Bus")
print(payload["evidence"])
