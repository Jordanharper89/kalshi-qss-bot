from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import apply_learning_inputs
from .slop_063_independent_token_idempotent_learning_admission import candidate_inputs

def apply_slop_inputs(state,root=None):
 root=Path(root or Path.cwd())
 rows=candidate_inputs(root)
 inputs=[x[3] for x in rows]
 if not inputs: return None,state,0
 last_ts=max(str(x[0]["frozen_at"]) for x in rows)
 result,new_state=apply_learning_inputs(
  state,inputs,last_ts,"SLOP:BUY_PRESSURE")
 return result,new_state,len(inputs)
