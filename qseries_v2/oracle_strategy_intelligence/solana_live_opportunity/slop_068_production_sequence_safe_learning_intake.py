from pathlib import Path
from .slop_062_native_ocl_prospective_outcome_bridge import build_slop_learning_input
from .slop_067_opportunity_level_exactly_once_learning_lineage import independent_evidence,load_consumed
def pending_inputs(state,root=None):
 root=Path(root or Path.cwd()); consumed=load_consumed(root)
 rows=[(k,e) for k,e in independent_evidence(root) if k not in consumed]
 seq=int(state.ocl_state.applied_through_sequence)
 out=[]
 for k,e in rows:
  seq+=1
  oo,ev,ri=build_slop_learning_input(seq,e)
  out.append((k,e,oo,ev,ri))
 return out
