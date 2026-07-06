from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline
from qseries_v2.oi.research_packet import research_packet_engine

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

decision = calibrated_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

packet = research_packet_engine.create(decision, evidence)

assert packet["packet_type"] == "oracle_research_packet"
assert packet["ticker"] == "TEST-MARKET"
assert packet["evidence_count"] == 3
assert packet["oracle_executes"] is False
assert "ORACLE RESEARCH REPORT" in packet["report"]

print("[PASS] OI-014 Research Packet Engine")
print({
    "ticker": packet["ticker"],
    "action": packet["action"],
    "confidence": packet["confidence"],
    "evidence_count": packet["evidence_count"],
    "oracle_executes": packet["oracle_executes"],
})
