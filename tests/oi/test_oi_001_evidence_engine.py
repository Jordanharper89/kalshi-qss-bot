from qseries_v2.oi.evidence_engine import Evidence, evidence_engine

evidence_engine.add(Evidence(
    source="unit_test",
    category="market",
    value={"edge":5.2}
))

assert len(evidence_engine.all())==1
print("[PASS] OI-001 Evidence Engine")
