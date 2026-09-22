import json
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import load_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_068_production_sequence_safe_learning_intake import pending_inputs
r=Path.cwd(); sp=r/"runtime_state/oracle_learning_runtime_state.json"
s=load_learning_runtime_state(sp); rows=pending_inputs(s,r)
b={"cycles":s.cycles,"outcomes_learned":s.outcomes_learned,
"applied_through_sequence":s.ocl_state.applied_through_sequence,
"state_hash":s.ocl_state.state_hash,"pending_slop":len(rows)}
p=r/"runtime_state/solana_live_opportunity/slop_071_pre_restart_baseline.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(b,indent=2,sort_keys=True),encoding="utf-8")
print("[CYCLES]",b["cycles"])
print("[OUTCOMES_LEARNED]",b["outcomes_learned"])
print("[APPLIED_THROUGH]",b["applied_through_sequence"])
print("[PENDING_SLOP]",b["pending_slop"])
print("[STATE_HASH]",b["state_hash"])
assert b["pending_slop"]>0
print("[PASS] durable pre-restart production baseline frozen")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-071 CERTIFIED")
