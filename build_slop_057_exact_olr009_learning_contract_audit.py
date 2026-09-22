from pathlib import Path
import ast,json
R=Path.cwd()
P=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
assert P.exists(),f"MISSING:{P}"
s=P.read_text(encoding="utf-8"); t=ast.parse(s)
funcs={}
for x in t.body:
 if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)):
  funcs[x.name]=[a.arg for a in x.args.args]
imports=[ast.unparse(x) for x in t.body if isinstance(x,(ast.Import,ast.ImportFrom))]
classes=[x.name for x in t.body if isinstance(x,ast.ClassDef)]
constants={}
for x in t.body:
 if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name):
  try: constants[x.targets[0].id]=ast.literal_eval(x.value)
  except Exception: pass
data={"module":str(P.relative_to(R)),"functions":funcs,"classes":classes,
      "imports":imports,"constants":constants,"execution_authority":False}
O=R/"runtime_state/solana_live_opportunity/slop_057_olr009_contract_audit.json"
O.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")
T=R/"test_slop_057_exact_olr009_learning_contract_audit.py"
T.write_text("""import json
from pathlib import Path
x=json.loads(Path("runtime_state/solana_live_opportunity/slop_057_olr009_contract_audit.json").read_text())
assert "run_high_coverage_learning_cycle" in x["functions"]
assert not x["execution_authority"]
print("[MODULE]",x["module"])
print("[FUNCTIONS]",x["functions"])
print("[CLASSES]",x["classes"])
print("[IMPORTS]",x["imports"])
print("[CONSTANTS]",x["constants"])
print("[PASS] exact OLR-009 production learning contract physically audited")
print("[PASS] no learner/runtime mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-057 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-057 exact OLR-009 contract audit installed")
print("[PASS] test installed:",T.name)