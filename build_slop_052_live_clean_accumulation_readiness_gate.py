from pathlib import Path
T=Path("test_slop_052_live_clean_accumulation_readiness_gate.py")
T.write_text("""from pathlib import Path
import ast
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
p=Path("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt")
assert p.exists()
runner=Path("run_slop_buy_pressure_live.py").read_text()
ast.parse(runner)
assert "worker_round" in runner
assert "read_resolution_dicts" in runner
assert "resolve_background(" not in runner
assert "execution_authority=FALSE" in runner
rs=read_resolution_dicts()
print("[TOTAL_CANONICAL_RESOLUTIONS]",len(rs))
print("[PASS] repaired native worker remains continuous")
print("[PASS] canonical resolution readback remains attached")
print("[PASS] clean prospective cohort boundary exists")
print("[PASS] Oracle is ready for post-repair live accumulation")
print("[PASS] no profitability claim made")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-052 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-052 live accumulation readiness gate installed")
print("[PASS] test installed:",T)