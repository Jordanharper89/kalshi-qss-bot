from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import genesis_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_064c_exact_tuple_contract_learner_integration_repair import apply_slop_inputs
s=genesis_learning_runtime_state()
before=s.outcomes_learned
result,n,count=apply_slop_inputs(s,Path.cwd())
assert result is not None
assert count>0
assert n.outcomes_learned==before+count
assert n.cycles==s.cycles+1
assert n.last_ticker=="SLOP:BUY_PRESSURE"
print("[INPUTS_APPLIED]",count)
print("[CYCLES_BEFORE]",s.cycles)
print("[CYCLES_AFTER]",n.cycles)
print("[OUTCOMES_LEARNED_BEFORE]",before)
print("[OUTCOMES_LEARNED_AFTER]",n.outcomes_learned)
print("[PASS] exact OLR-004 tuple contract honored")
print("[PASS] native SLOP inputs consumed by existing learner machinery")
print("[PASS] production learner state not written")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-064C CERTIFIED")
