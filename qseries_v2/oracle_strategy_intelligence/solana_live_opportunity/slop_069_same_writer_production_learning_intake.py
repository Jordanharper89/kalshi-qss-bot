from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import apply_learning_inputs
from .slop_067_opportunity_level_exactly_once_learning_lineage import load_consumed,save_consumed
from .slop_068_production_sequence_safe_learning_intake import pending_inputs
def apply_pending_slop(state,root=None,progress=print,persist=True):
 root=Path(root or Path.cwd()); rows=pending_inputs(state,root)
 if not rows: return None,state,0
 inputs=tuple(x[4] for x in rows)
 last=max(rows,key=lambda x:(str(x[1]["frozen_at"]),x[1]["prediction_id"]))
 result,new=apply_learning_inputs(state,inputs,str(last[1]["frozen_at"]),"SLOP:BUY_PRESSURE")
 if persist:
  d=load_consumed(root)
  for k,e,oo,ev,ri in rows:
   d[k]={"prediction_id":e["prediction_id"],"token_address":e["token_address"],
    "event_id":ev.event_id,"input_hash":ri.input_hash,"status":"learned"}
  save_consumed(d,root)
 progress(f"[SLOP LEARN] outcomes={len(rows)} cycle={new.cycles} learned_total={new.outcomes_learned}")
 return result,new,len(rows)
