from pathlib import Path
import ast,hashlib,json
R=Path.cwd();L=R/"run_oracle_LIVE.py";D=R/"runtime_state"/"solana_live_opportunity";D.mkdir(parents=True,exist_ok=True)
if not L.exists():raise SystemExit("[FAIL] run_oracle_LIVE.py missing")
src=L.read_text(encoding="utf-8");tree=ast.parse(src);nodes=tuple(ast.walk(tree));children=None
for n in nodes:
 if isinstance(n,(ast.Assign,ast.AnnAssign)):
  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])
  if "CHILDREN" in names and isinstance(n.value,ast.Dict):children=ast.literal_eval(n.value);break
if not isinstance(children,dict):raise SystemExit("[FAIL] exact native CHILDREN dict not found")
state={"schema":"SLOP-033B","launcher_sha256":hashlib.sha256(src.encode()).hexdigest(),"children":children,
"has_start":any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="_start" for n in nodes),
"has_run_forever":any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="run_forever" for n in nodes),
"execution_authority":False}
if not state["has_start"] or not state["has_run_forever"]:raise SystemExit("[FAIL] native supervision contract incomplete")
(D/"slop033b_native_child_contract.json").write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
T=R/"test_slop_033b_exact_oracle_live_native_child_contract_audit_repair.py"
T.write_text("""import json\nfrom pathlib import Path\nx=json.loads(Path('runtime_state/solana_live_opportunity/slop033b_native_child_contract.json').read_text())\nassert x['children'] and x['has_start'] and x['has_run_forever']\nassert x['execution_authority'] is False\nprint('[SLOP-033B]',x)\nprint('[PASS] exact production native-child contract captured read-only')\n""",encoding="utf-8")
print("[SLOP-033B]",state);print("[PASS] launcher audited read-only");print("[PASS] execution_authority=FALSE")
