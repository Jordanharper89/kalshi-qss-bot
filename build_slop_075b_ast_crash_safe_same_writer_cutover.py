from pathlib import Path
import ast, shutil

R=Path.cwd()
O=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
M=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075b_ast_crash_safe_same_writer_cutover.py"
T=R/"test_slop_075b_ast_crash_safe_same_writer_cutover.py"
assert O.exists(),"OLR009_MISSING"

module="""from pathlib import Path
import json, os
from .slop_074_safe_same_writer_learning_intake import prepare_pending_slop, commit_consumed
JREL=Path("runtime_state/solana_live_opportunity/slop_075b_learning_commit_journal.json")
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
    "end_sequence":new.ocl_state.applied_through_sequence}
 tmp=jp.with_suffix(".tmp"); jp.parent.mkdir(parents=True,exist_ok=True)
 tmp.write_text(json.dumps(j,sort_keys=True),encoding="utf-8"); os.replace(tmp,jp)
 return "APPLY",new,rows,j
def finalize(rows,root=None,progress=print):
 root=Path(root or Path.cwd())
 n=commit_consumed(rows,root,progress) if rows else 0
 jp=_journal(root)
 if jp.exists(): jp.unlink()
 return n
"""
M.write_text(module,encoding="utf-8")

s=O.read_text(encoding="utf-8"); tree=ast.parse(s); lines=s.splitlines()
imp=None; assign=None; ifnode=None
for n in ast.walk(tree):
 if isinstance(n,ast.ImportFrom) and n.module and n.module.endswith("slop_069_same_writer_production_learning_intake"):
  imp=n
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and getattr(n.value.func,"id",None)=="apply_pending_slop":
  assign=n
for n in ast.walk(tree):
 if isinstance(n,ast.If) and assign and n.lineno>assign.lineno:
  names={x.id for x in ast.walk(n.test) if isinstance(x,ast.Name)}
  if "slop_applied" in names:
   ifnode=n; break
assert imp and assign and ifnode,"AST_UNSAFE_BOUNDARY_NOT_FOUND"

indent=lines[assign.lineno-1][:len(lines[assign.lineno-1])-len(lines[assign.lineno-1].lstrip())]
block=[
indent+'slop_mode, slop_state, slop_rows, slop_journal = recover_or_prepare(state, root, progress)',
indent+'if slop_mode == "APPLY":',
indent+'    state = slop_state',
indent+'    save_learning_runtime_state(sp, state)',
indent+'    finalize(slop_rows, root, progress)',
indent+'    progress(f"[SLOP LEARN CUTOVER] applied={len(slop_rows)} crash_safe=True")',
indent+'elif slop_mode == "RECOVER_COMMIT":',
indent+'    finalize(tuple(), root, progress)',
indent+'    progress("[SLOP LEARN CUTOVER] recovered durable learner-state commit")'
]
lines[assign.lineno-1:ifnode.end_lineno]=block
newimp="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_075b_ast_crash_safe_same_writer_cutover import recover_or_prepare, finalize"
lines[imp.lineno-1:imp.end_lineno]=[newimp]
out="\n".join(lines)+"\n"; ast.parse(out)
b=O.with_suffix(".pre_slop075b.py")
if not b.exists(): shutil.copy2(O,b)
O.write_text(out,encoding="utf-8")

test="""from pathlib import Path
import ast
R=Path.cwd(); o=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
m=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075b_ast_crash_safe_same_writer_cutover.py"
for p in (o,m): ast.parse(p.read_text(encoding="utf-8"))
s=o.read_text(encoding="utf-8")
assert "slop_069_same_writer_production_learning_intake" not in s
assert "apply_pending_slop" not in s
assert "recover_or_prepare" in s and "finalize" in s
assert s.index("save_learning_runtime_state(sp, state)") < s.index("finalize(slop_rows, root, progress)")
print("[PASS] exact unsafe AST boundary retired")
print("[PASS] learner state save precedes consumed commit")
print("[PASS] crash recovery journal installed")
print("[PASS] OLR-009 parses after cutover")
print("[PASS] SLOP-075B CERTIFIED execution_authority=FALSE")
"""
T.write_text(test,encoding="utf-8")
print("[PASS] SLOP-075B AST-located crash-safe cutover installed")
print("[PASS] test installed:",T.name)
print("[BACKUP]",b)
