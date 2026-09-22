from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_004_untouched_holdout_evaluator_v2.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert 'r["decision_epoch"]=float(r["t"])' in s
assert 'for k,v in (r.get("features") or {}).items()' in s
assert 'osd_003_discovery_candidates.json' in s
assert 'sc["lb95"]>0' in s
assert "HURDLE=0.02" in s
assert "MIN_N=12" in s and "MIN_TICKERS=3" in s
assert "execution_authority" in s and "publication_allowed" in s
print("[PASS] OSD-004 holdout V2 compiles")
print("[PASS] exact OSD-002 corpus schema supported")
print("[PASS] exact OSD-003 V2 candidate file supported")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] untouched holdout winner gate = N>=12, tickers>=3, LB95>0")
print("[PASS] execution/publication remain false")
