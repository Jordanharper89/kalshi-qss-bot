from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

result = calibrated_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert result["ticker"] == "TEST-MARKET"
assert result["adjusted_confidence"] > 0
assert "recommendation" in result
assert result["oracle_executes"] is False

print("[PASS] OI-012 Calibrated Decision Pipeline")
print(result["recommendation"])
print(result["calibration"])
