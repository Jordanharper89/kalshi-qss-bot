from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline
from qseries_v2.oi.research_report import research_report_engine

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

report = research_report_engine.generate(decision)

assert "ORACLE RESEARCH REPORT" in report
assert "TEST-MARKET" in report
assert "Oracle does not execute trades" in report

print("[PASS] OI-013 Research Report Engine")
print(report)
