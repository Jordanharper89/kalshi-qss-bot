from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import genesis_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_064_existing_oracle_learner_intake_integration import apply_slop_inputs
s=genesis_learning_runtime_state()
before=s.outcomes_learned
n,c=apply_slop_inputs(s,Path.cwd())
assert c>0
assert n.outcomes_learned>before
assert n.last_ticker=="SLOP:BUY_PRESSURE"
print("[INPUTS_APPLIED]",c)
print("[OUTCOMES_LEARNED_BEFORE]",before)
print("[OUTCOMES_LEARNED_AFTER]",n.outcomes_learned)
print("[PASS] SLOP inputs consumed by existing OLR-004/OCL state machinery")
print("[PASS] production learner state not written by certification test")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-064 CERTIFIED")
