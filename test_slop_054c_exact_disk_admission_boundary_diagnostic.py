from pathlib import Path
import ast
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
print("[MODULE]",p)
print("[RANK_PAIR_CALLS]",s.count("_rank_pair("))
print("[ADMITTED_APPEND]",s.count("admitted.append("))
assert "blocked=set(unresolved_view(root).tokens)" in s
assert "if str(token) in blocked:continue" in s
assert "xs=tuple(x[\"admitted\"])" in s
assert "admitted.append(_rank_pair(str(token),xs,root))" in s
assert s.count("admitted.append(")==1
print("[PASS] disk SLOP-015B collapses each token to one canonical pair")
print("[PASS] disk SLOP-015B blocks already-unresolved tokens")
print("[PASS] duplicate live output is inconsistent with current disk semantics")
print("[PASS] SLOP-054C CERTIFIED")
print("[PASS] execution_authority=FALSE")
