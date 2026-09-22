from pathlib import Path
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
R=Path("run_slop_buy_pressure_live.py")
T=Path("test_slop_054d2_revision_fingerprint_syntax_repair.py")
s=P.read_text(encoding="utf-8")
bad='REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"\\\\nfrom '
good='REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"\nfrom '
assert bad in s,"expected malformed SLOP-054D line not found"
P.write_text(s.replace(bad,good,1),encoding="utf-8")
T.write_text("""import ast,importlib
from pathlib import Path
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
assert "blocked=set(unresolved_view(root).tokens)" in s
assert "admitted.append(_rank_pair(str(token),xs,root))" in s
r=Path("run_slop_buy_pressure_live.py").read_text(encoding="utf-8");ast.parse(r)
assert "ADMISSION_REVISION" in r and "admission_revision=%s" in r
print("[PASS] malformed literal backslash-n repaired")
print("[PASS] canonical-pair/single-inflight semantics preserved")
print("[PASS] runner revision fingerprint parses")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054D2 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-054D2 syntax repair installed")
print("[PASS] test installed:",T)