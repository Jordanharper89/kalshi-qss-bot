from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.confidence_engine import confidence_engine

evidence = [
    Evidence(source="Market", category="market", value={}),
    Evidence(source="History", category="historical", value={}),
    Evidence(source="News", category="news", value={})
]

score = confidence_engine.score(evidence)

assert score > 0

print(f"[PASS] OI-002 Confidence Engine ({score}%)")
