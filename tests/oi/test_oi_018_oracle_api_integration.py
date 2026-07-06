from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.oracle_api_integration import oracle_api_integration

boot = oracle_api_integration.bootstrap()

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

packet = oracle_api_integration.analyze(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

service = oracle_api_integration.get_service()

assert boot["status"] == "ready"
assert boot["service_id"] == "oracle.intelligence"
assert packet["packet_type"] == "oracle_research_packet"
assert packet["oracle_executes"] is False
assert service is not None

print("[PASS] OI-018 Oracle API Integration")
print({
    "boot": boot,
    "ticker": packet["ticker"],
    "action": packet["action"],
    "confidence": packet["confidence"],
})
