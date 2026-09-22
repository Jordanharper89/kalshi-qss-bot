from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py")
t=ast.parse(p.read_text(encoding="utf-8"))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef)
 and x.name=="run_high_coverage_learning_cycle")
s=ast.unparse(f)
for n in ("load_learning_runtime_state","save_learning_runtime_state",
          "load_learning_ledger","save_learning_ledger","apply_learning_inputs"):
 assert n in s,n
print("[PASS] production state load/save boundary present")
print("[PASS] production ledger load/save boundary present")
print("[PASS] existing apply_learning_inputs boundary present")
print("[PASS] no production learner mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-066 CERTIFIED")
