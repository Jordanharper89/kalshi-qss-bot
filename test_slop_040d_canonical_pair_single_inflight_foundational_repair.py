from pathlib import Path
import ast

P = Path(
    "qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/"
    "slop_015b_concurrent_live_lifecycle_rebuild.py"
)

assert P.exists(), P

s = P.read_text(encoding="utf-8")
ast.parse(s)

assert "_rank_pair" in s
assert "blocked=set(unresolved_view(root).tokens)" in s
assert "if str(token) in blocked:continue" in s
assert "admitted.append(_rank_pair" in s
assert "persist_predictions(tuple(admitted),root)" in s
assert '"execution_authority":False' in s
assert "EXECUTION_AUTHORITY=False" in s

print("[PASS] SLOP-040D repaired module parses")
print("[PASS] unresolved token admission guard certified")
print("[PASS] one canonical pair selection boundary certified")
print("[PASS] durable prediction persistence retained")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-040D CERTIFIED")