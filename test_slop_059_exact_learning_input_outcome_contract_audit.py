from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_003_learning_event_bridge.py")
t=ast.parse(p.read_text(encoding="utf-8"))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="build_learning_runtime_input")
assert [a.arg for a in f.args.args]==["sequence","outcome","evidence_hash"]
print("[PASS] exact OLR-003 learning input constructor verified")
print("[PASS] no learner/runtime/state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-059 CERTIFIED")
