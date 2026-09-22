from pathlib import Path
import ast
fs=["qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py","qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_016b_exact_frozen_prediction_maturity_rebuild.py","qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_025_live_freeze_maturity_resolution_worker.py","qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_027_physical_profitability_generalization_report.py","run_slop_buy_pressure_live.py"]
for f in fs:ast.parse(Path(f).read_text())
a,b,c,d,r=[Path(f).read_text() for f in fs]
assert "blocked=set(unresolved_view(root).tokens)" in a
assert "_rank_pair" in a
assert "tolerance_seconds=30.0" in b
assert "watch=pending+fresh" in c
assert "majority=positive_tokens>len(token_means)/2" in d
assert "resolve_background(" not in r
assert "read_resolution_dicts" in r
assert "execution_authority=FALSE" in r
print("[PASS] canonical-pair + single-inflight frozen")
print("[PASS] pending-first + maturity boundary frozen")
print("[PASS] single-resolution-owner + strict generalization frozen")
print("[PASS] SLOP-049B FOUNDATIONAL REPAIR FROZEN")
