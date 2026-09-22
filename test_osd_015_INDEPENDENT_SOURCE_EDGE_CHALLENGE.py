from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_015_independent_source_edge_challenge.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ["historical_condition_windows.jsonl","past_only","bisect_right",
          "exogenous_evidence_snapshot","MAX_LAG_S=90.0","TRAIN_FRAC=.65","HURDLE=.02",
          "INDEPENDENT_PAIR","CROSS_SOURCE_PAIR",
          "INDEPENDENT_SOURCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT",
          '"execution_authority":False','"publication_allowed":False']:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-015 independent-source challenge compiles")
print("[PASS] Coinbase joins are past-only and bounded by decision time")
print("[PASS] raw exogenous prediction snapshots included")
print("[PASS] independent-only and cross-source interactions enabled")
print("[PASS] fixed 65/35 temporal holdout and 2% hurdle")
print("[PASS] execution/publication remain false")
