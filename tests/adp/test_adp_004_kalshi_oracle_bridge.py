from qseries_v2.adapters.kalshi_oracle_bridge import kalshi_oracle_bridge
from qseries_v2.oi.evidence_engine import evidence_engine, Evidence

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Oracle Bridge Test",
    "yes_price": 71,
    "volume": 1500,
}

evidence = kalshi_oracle_bridge.ingest_market(raw)

assert isinstance(evidence, Evidence)
assert evidence.source == "kalshi"
assert evidence.category == "market"
assert evidence.value["ticker"] == "TEST-KALSHI"
assert evidence.value["yes_price"] == 71.0
assert len(evidence_engine.all()) >= 1

print("[PASS] ADP-004 Kalshi Oracle Evidence Bridge")
print(evidence)
