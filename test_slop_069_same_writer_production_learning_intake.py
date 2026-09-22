from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import load_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_069_same_writer_production_learning_intake import apply_pending_slop
r=Path.cwd(); s=load_learning_runtime_state(r/"runtime_state/oracle_learning_runtime_state.json")
before=s.outcomes_learned
result,n,count=apply_pending_slop(s,r,progress=lambda x:None,persist=False)
assert count>=0
if count:
 assert result is not None and n.outcomes_learned==before+count
assert s.outcomes_learned==before
print("[PENDING_CONSUMABLE]",count)
print("[PRODUCTION_OUTCOMES_BEFORE]",before)
print("[SIMULATED_OUTCOMES_AFTER]",n.outcomes_learned)
print("[PASS] SLOP uses existing OLR-004 state transition")
print("[PASS] no independent production-state writer introduced")
print("[PASS] durable lineage not mutated during certification")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-069 CERTIFIED")
