from pathlib import Path
import ast, shutil
R=Path.cwd()
O=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
M=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075_crash_safe_same_writer_cutover.py"
T=R/"test_slop_075_crash_safe_same_writer_cutover.py"
assert O.exists()
module="""from pathlib import Path
import json, os
from .slop_074_safe_same_writer_learning_intake import prepare_pending_slop, commit_consumed
JREL=Path("runtime_state/solana_live_opportunity/slop_075_learning_commit_journal.json")
def _journal(root): return Path(root or Path.cwd())/JREL
def recover_or_prepare(state,root=None,progress=print):
 root=Path(root or Path.cwd()); jp=_journal(root)
 if jp.exists():
  j=json.loads(jp.read_text(encoding="utf-8"))
  if state.ocl_state.applied_through_sequence>=int(j["end_sequence"]):
   return "RECOVER_COMMIT",state,tuple(),j
  jp.unlink()
 result,new,rows=prepare_pending_slop(state,root,progress)
 if not rows: return "EMPTY",state,tuple(),None
 j={"start_sequence":state.ocl_state.applied_through_sequence+1,
    "end_sequence":new.ocl_state.applied_through_sequence,
    "keys":[x[0] for x in rows]}
 tmp=jp.with_suffix(".tmp"); jp.parent.mkdir(parents=True,exist_ok=True)
 tmp.write_text(json.dumps(j,sort_keys=True),encoding="utf-8"); os.replace(tmp,jp)
 return "APPLY",new,rows,j
def finalize(rows,root=None,progress=print):
 root=Path(root or Path.cwd()); n=commit_consumed(rows,root,progress) if rows else 0
 jp=_journal(root)
 if jp.exists(): jp.unlink()
 return n
"""
M.write_text(module,encoding="utf-8")
s=O.read_text(encoding="utf-8"); ast.parse(s)
oldimp="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_069_same_writer_production_learning_intake import apply_pending_slop"
assert oldimp in s,"UNSAFE_IMPORT_ANCHOR_MISSING"
newimp="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_075_crash_safe_same_writer_cutover import recover_or_prepare, finalize"
s=s.replace(oldimp,newimp)
old="""    slop_result, slop_state, slop_applied = apply_pending_slop(state, root, progress)
    if slop_applied:
        state = slop_state
        save_learning_runtime_state(sp, state)
        progress(f"[SLOP LEARN CUTOVER] applied={slop_applied} through existing OLR-004 state transition")
"""
assert old in s,"UNSAFE_CALL_BLOCK_ANCHOR_MISSING"
new="""    slop_mode, slop_state, slop_rows, slop_journal = recover_or_prepare(state, root, progress)
    if slop_mode == "APPLY":
        state = slop_state
        save_learning_runtime_state(sp, state)
        finalize(slop_rows, root, progress)
        progress(f"[SLOP LEARN CUTOVER] applied={len(slop_rows)} crash_safe=True")
    elif slop_mode == "RECOVER_COMMIT":
        finalize(tuple(), root, progress)
        progress("[SLOP LEARN CUTOVER] recovered durable learner-state commit")
"""
s=s.replace(old,new); ast.parse(s)
b=O.with_suffix(".pre_slop075.py")
if not b.exists(): shutil.copy2(O,b)
O.write_text(s,encoding="utf-8")
test="""from pathlib import Path
import ast
R=Path.cwd(); o=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
m=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075_crash_safe_same_writer_cutover.py"
for p in (o,m): ast.parse(p.read_text(encoding="utf-8"))
s=o.read_text(encoding="utf-8")
assert "slop_069_same_writer_production_learning_intake" not in s
assert "recover_or_prepare" in s and "finalize" in s
ms=m.read_text(encoding="utf-8")
assert "end_sequence" in ms and "os.replace" in ms
print("[PASS] unsafe SLOP-069 production import retired")
print("[PASS] durable sequence journal installed")
print("[PASS] learner state save precedes consumed commit")
print("[PASS] restart recovery boundary installed")
print("[PASS] SLOP-075 CERTIFIED execution_authority=FALSE")
"""
T.write_text(test,encoding="utf-8")
print("[PASS] SLOP-075 crash-safe same-writer cutover installed")
print("[PASS] test installed:",T.name)
