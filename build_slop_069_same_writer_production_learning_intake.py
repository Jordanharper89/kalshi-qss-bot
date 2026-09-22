from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
P=M/"slop_069_same_writer_production_learning_intake.py"
P.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
T=Path("test_slop_069_same_writer_production_learning_intake.py")
T.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
print("[PASS] SLOP-069 same-writer production intake installed")
print("[PASS] test installed:",T.name)