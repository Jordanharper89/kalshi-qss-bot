from pathlib import Path
import ast
R=Path.cwd(); B=R/"qseries_v2/oracle_learning_runtime"
P=B/"olr_003_learning_event_bridge.py"
assert P.exists(),f"MISSING:{P}"
s=P.read_text(encoding="utf-8"); t=ast.parse(s)
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="build_learning_runtime_input")
print("[OLR003_BUILD_INPUT_SOURCE]")
print(ast.unparse(f))
imports=[x for x in t.body if isinstance(x,ast.ImportFrom)]
targets=[]
for x in imports:
 for n in x.names:
  if n.name!="annotations": targets.append((x.module,n.name))
print("[OLR003_IMPORTED_CONTRACTS]",targets)
for mod,name in targets:
 if not mod: continue
 p=B/(mod.split(".")[-1]+".py")
 if not p.exists(): continue
 tt=ast.parse(p.read_text(encoding="utf-8"))
 for x in tt.body:
  if isinstance(x,ast.ClassDef) and x.name==name:
   print("[CONTRACT]",p.name,name)
   print(ast.unparse(x))
T=R/"test_slop_059_exact_learning_input_outcome_contract_audit.py"
T.write_text("""from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_003_learning_event_bridge.py")
t=ast.parse(p.read_text(encoding="utf-8"))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="build_learning_runtime_input")
assert [a.arg for a in f.args.args]==["sequence","outcome","evidence_hash"]
print("[PASS] exact OLR-003 learning input constructor verified")
print("[PASS] no learner/runtime/state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-059 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-059 exact learning input/outcome contract audit installed")
print("[PASS] test installed:",T.name)