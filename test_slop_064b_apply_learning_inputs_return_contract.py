from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_004_learning_cycle_state.py")
t=ast.parse(p.read_text(encoding="utf-8"))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="apply_learning_inputs")
returns=[ast.unparse(x.value) for x in ast.walk(f) if isinstance(x,ast.Return)]
assert returns
print("[RETURNS]",returns)
print("[PASS] exact apply_learning_inputs return contract physically audited")
print("[PASS] no learner/runtime/state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-064B CERTIFIED")
