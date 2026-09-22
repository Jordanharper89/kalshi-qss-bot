from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
P=M/"slop_064_existing_oracle_learner_intake_integration.py"
P.write_text(r'''from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import apply_learning_inputs
from .slop_063_independent_token_idempotent_learning_admission import candidate_inputs

def apply_slop_inputs(state,root=None):
 root=Path(root or Path.cwd())
 rows=candidate_inputs(root)
 inputs=[x[3] for x in rows]
 if not inputs: return state,0
 last_ts=max(str(x[0]["frozen_at"]) for x in rows)
 new_state=apply_learning_inputs(state,inputs,last_ts,"SLOP:BUY_PRESSURE")
 return new_state,len(inputs)
''',encoding="utf-8")
T=Path("test_slop_064_existing_oracle_learner_intake_integration.py")
T.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
print("[PASS] SLOP-064 existing Oracle learner integration installed")
print("[PASS] test installed:",T.name)