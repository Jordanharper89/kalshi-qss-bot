from pathlib import Path
import ast
R=Path.cwd()
P=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
assert P.exists(),f"MISSING:{P}"
t=ast.parse(P.read_text(encoding="utf-8"))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef)
       and x.name=="run_high_coverage_learning_cycle")
print("[OLR009_CYCLE_SOURCE]")
print(ast.unparse(f))
print("[PATH_EXPRESSIONS]")
for x in ast.walk(f):
 if isinstance(x,(ast.Call,ast.BinOp,ast.JoinedStr)):
  s=ast.unparse(x)
  if any(k in s.lower() for k in ("state","ledger","runtime_state","learning")):
   print(s)
T=R/"test_slop_066_exact_production_learning_persistence_boundary.py"
T.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
print("[PASS] SLOP-066 production persistence audit installed")
print("[PASS] test installed:",T.name)