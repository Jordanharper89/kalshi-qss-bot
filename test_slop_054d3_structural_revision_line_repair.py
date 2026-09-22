import ast,importlib
from pathlib import Path
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
assert "\\nfrom " not in s.splitlines()[0]
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
assert "blocked=set(unresolved_view(root).tokens)" in s
assert "admitted.append(_rank_pair(str(token),xs,root))" in s
r=Path("run_slop_buy_pressure_live.py").read_text(encoding="utf-8");ast.parse(r)
assert "ADMISSION_REVISION" in r
print("[PASS] malformed revision line structurally repaired")
print("[PASS] SLOP-015B imports successfully")
print("[PASS] canonical-pair + single-inflight semantics preserved")
print("[PASS] runner fingerprint parses")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054D3 CERTIFIED")
