from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_011_oracle_prediction_truth_audit_v2.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for needle in [
    "CORPUS_COVERAGE_LOW",
    "TEMPORAL_LINEAGE_VIOLATION",
    "TWO_PERCENT_OPPORTUNITY_RARE",
    "FEATURE_MISSINGNESS",
    "DUPLICATE_FEATURES",
    "EVIDENCE_COLLAPSE_IN_CORPUS",
    "POSTGRES_FRESHNESS_NOT_VERIFIED",
    "oracle_canonical_observations",
    "source_id <> 'source.kalshi.market_data'",
    '"execution_authority":False',
    '"publication_allowed":False'
]:
    assert needle in s, needle
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-011 truth audit V2 compiles")
print("[PASS] corpus coverage audit installed")
print("[PASS] timestamp/anti-leakage audit installed")
print("[PASS] 2% opportunity-density audit installed")
print("[PASS] feature health/evidence-collapse audit installed")
print("[PASS] optional read-only PostgreSQL freshness audit installed")
print("[PASS] execution/publication remain false")
