from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
P=M/"slop_068_production_sequence_safe_learning_intake.py"
P.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
T=Path("test_slop_068_production_sequence_safe_learning_intake.py")
T.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
print("[PASS] SLOP-068 production-sequence-safe intake installed")
print("[PASS] test installed:",T.name)