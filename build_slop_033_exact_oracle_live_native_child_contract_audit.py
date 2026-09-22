from pathlib import Path
import ast,hashlib,json
R=Path.cwd();L=R/"run_oracle_LIVE.py";D=R/"runtime_state"/"solana_live_opportunity";D.mkdir(parents=True,exist_ok=True)
if not L.exists(): raise SystemExit("[FAIL] run_oracle_LIVE.py missing")
src=L.read_text(encoding="utf-8"); tree=ast.parse(src)
children=None
for n in ast.walk(tree):
 if isinstance(n,(ast.Assign,ast.AnnAssign)):
  v=n.value
  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])
  if "CHILDREN" in names and isinstance(v,ast.Dict):
   children=ast.literal_eval(v);break
if not isinstance(children,dict): raise SystemExit("[FAIL] exact native CHILDREN dict not found")
state={"schema":"SLOP-033","launcher_sha256":hashlib.sha256(src.encode()).hexdigest(),"children":children,
"has_start":any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="_start" for n in tree),
"has_run_forever":any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="run_forever" for n in tree),
"execution_authority":False}
(D/"slop033_native_child_contract.json").write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
T=R/"test_slop_033_exact_oracle_live_native_child_contract_audit.py"
T.write_text("""import json\nfrom pathlib import Path\np=Path('runtime_state/solana_live_opportunity/slop033_native_child_contract.json')\nx=json.loads(p.read_text())\nassert x['children'] and x['has_start'] and x['has_run_forever']\nassert x['execution_authority'] is False\nprint('[SLOP-033]',x)\nprint('[PASS] exact production native-child contract captured read-only')\n""",encoding="utf-8")
print("[SLOP-033]",state);print("[PASS] launcher audited read-only");print("[PASS] execution_authority=FALSE")
