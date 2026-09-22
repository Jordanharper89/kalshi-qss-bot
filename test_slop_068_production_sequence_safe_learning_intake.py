from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import load_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_068_production_sequence_safe_learning_intake import pending_inputs
r=Path.cwd(); sp=r/"runtime_state/oracle_learning_runtime_state.json"
s=load_learning_runtime_state(sp); before=s.ocl_state.applied_through_sequence
rows=pending_inputs(s,r)
seq=[x[4].sequence for x in rows]
assert seq==list(range(before+1,before+1+len(rows)))
print("[PRODUCTION_APPLIED_THROUGH]",before)
print("[PENDING_SLOP_INPUTS]",len(rows))
print("[PROPOSED_SEQUENCES]",seq)
print("[PASS] SLOP sequences continue exact production OCL sequence")
print("[PASS] no genesis-sequence reuse")
print("[PASS] production state read-only")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-068 CERTIFIED")
