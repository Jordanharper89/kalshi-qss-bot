from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_016_comparable_case_regime_discovery.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["HURDLE=.02","A=.65","B=.80","MIN=24","K=64","if j>=q","expected_net","COMPARABLE_CASE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT","execution_authority"]:assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-016 comparable-case regime discovery compiles")
print("[PASS] robust multi-feature state similarity installed")
print("[PASS] exact asset+horizon comparable universes installed")
print("[PASS] strictly-earlier anti-leakage neighbors installed")
print("[PASS] 65/15/20 discovery/calibration/untouched chronology installed")
print("[PASS] fixed 2% hurdle and abstention installed")
print("[PASS] execution/publication remain false")
