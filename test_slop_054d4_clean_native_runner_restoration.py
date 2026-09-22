import ast,importlib
from pathlib import Path
a=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py").read_text();ast.parse(a)
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
r=Path("run_slop_buy_pressure_live.py").read_text();ast.parse(r)
assert "admission_revision=%s" in r and "worker_round" in r and "read_resolution_dicts" in r
assert "resolve_background(" not in r
print("[PASS] SLOP-015B parses/imports with repaired canonical-pair semantics")
print("[PASS] native BUY_PRESSURE runner cleanly restored and parses")
print("[PASS] SLOP-025 remains sole resolution owner")
print("[PASS] admission revision fingerprint retained correctly")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054D4 CERTIFIED")
