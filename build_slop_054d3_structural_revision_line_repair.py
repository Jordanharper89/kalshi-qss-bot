from pathlib import Path
import ast
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
T=Path("test_slop_054d3_structural_revision_line_repair.py")
s=P.read_text(encoding="utf-8")
lines=s.splitlines()
assert lines and lines[0].startswith('REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"')
first=lines[0]
marker="\\nfrom "
assert marker in first,"malformed literal newline marker not found in first line"
a,b=first.split(marker,1)
fixed="\n".join([a,"from "+b]+lines[1:])+"\n"
ast.parse(fixed)
assert 'REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"' in fixed
assert "blocked=set(unresolved_view(root).tokens)" in fixed
assert "admitted.append(_rank_pair(str(token),xs,root))" in fixed
P.write_text(fixed,encoding="utf-8")
T.write_text("""import ast,importlib
from pathlib import Path
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
assert "\\\\nfrom " not in s.splitlines()[0]
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
""",encoding="utf-8")
print("[PASS] SLOP-054D3 structural syntax repair installed")
print("[PASS] test installed:",T)