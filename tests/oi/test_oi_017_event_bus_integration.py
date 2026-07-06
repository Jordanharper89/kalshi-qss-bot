from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.event_bus_integration import oracle_event_bus
from qseries_v2.core.event_bus import event_bus

events = []

def handler(payload):
    events.append(payload)

event_bus.subscribe("oracle.analysis.completed", handler)

evidence = [
    Evidence(source="Market", category="market", value={"move":"up"}),
    Evidence(source="News", category="news", value={"tone":"positive"}),
    Evidence(source="History", category="historical", value={"pattern":"matched"}),
]

packet = oracle_event_bus.analyze(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert len(events) == 1
assert events[0]["ticker"] == "TEST-MARKET"
assert packet["action"] == "BUY_YES"

print("[PASS] OI-017 Event Bus Integration")
print(events[0])
