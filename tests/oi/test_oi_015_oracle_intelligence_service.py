from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.oracle_intelligence_service import oracle_intelligence_service

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

packet = oracle_intelligence_service.analyze(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

health = oracle_intelligence_service.health()

assert packet["packet_type"] == "oracle_research_packet"
assert packet["ticker"] == "TEST-MARKET"
assert packet["oracle_executes"] is False
assert health["status"] == "ready"

print("[PASS] OI-015 Oracle Intelligence Service")
print({
    "ticker": packet["ticker"],
    "action": packet["action"],
    "confidence": packet["confidence"],
    "health": health,
})
