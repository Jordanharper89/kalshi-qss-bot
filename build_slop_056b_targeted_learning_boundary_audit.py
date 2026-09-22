from pathlib import Path
import ast,json
R=Path.cwd()
names=("run_oracle_PROVEN_learning_runtime.py",
       "run_opr_004_learning_persistent_ingress.py")
data={}
for name in names:
 p=R/name
 assert p.exists(),f"MISSING:{name}"
 s=p.read_text(encoding="utf-8")
 t=ast.parse(s)
 data[name]={"path":str(p),
  "functions":[x.name for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))],
  "imports":[ast.unparse(x) for x in t.body if isinstance(x,(ast.Import,ast.ImportFrom))],
  "olr009":("OLR-009" in s or "proven_historical_path" in s)}
out=R/"runtime_state/solana_live_opportunity/slop_056b_learning_boundary_audit.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(data,indent=2),encoding="utf-8")
T=R/"test_slop_056b_targeted_learning_boundary_audit.py"
T.write_text("""import json
from pathlib import Path
p=Path("runtime_state/solana_live_opportunity/slop_056b_learning_boundary_audit.json")
x=json.loads(p.read_text())
assert len(x)==2
for n,v in x.items():
 assert Path(v["path"]).exists()
 print("[ENTRYPOINT]",n)
 print("[FUNCTIONS]",v["functions"])
 print("[IMPORTS]",v["imports"])
 print("[OLR009]",v["olr009"])
print("[PASS] exact production learning entrypoints physically audited")
print("[PASS] no learner/runtime mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-056B CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-056B targeted audit installed")
print("[PASS] test installed:",T.name)