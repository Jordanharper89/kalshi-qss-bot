from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.decision_pipeline import oracle_decision_pipeline

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

result = oracle_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert result["ticker"] == "TEST-MARKET"
assert result["confidence"] > 0
assert result["fair_yes_price"] > 0
assert result["recommendation"]["oracle_executes"] is False
assert "TEST-MARKET" in result["explanation"]

print("[PASS] OI-006 Oracle Decision Pipeline")
print(result["recommendation"])
print()
print(result["explanation"])
