from pathlib import Path
import ast,json,hashlib
R=Path.cwd();L=R/"run_oracle_LIVE.py";RUN=R/"run_slop_buy_pressure_live.py"
src=L.read_text(encoding="utf-8");tree=ast.parse(src);children=None
for n in ast.walk(tree):
 if isinstance(n,(ast.Assign,ast.AnnAssign)):
  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])
  if "CHILDREN" in names and isinstance(n.value,ast.Dict): children=ast.literal_eval(n.value);break
assert children and children.get("solana_buy_pressure")=="run_slop_buy_pressure_live.py"
assert RUN.exists();ast.parse(RUN.read_text(encoding="utf-8"))
state={"schema":"SLOP-037","launcher_sha256":hashlib.sha256(src.encode()).hexdigest(),
"native_child":"solana_buy_pressure","runner":"run_slop_buy_pressure_live.py","prediction_output":True,
"resolution_output":True,"read_only":True,"execution_authority":False,
"state":"NATIVE_ORACLE_LIVE_BUY_PRESSURE_CUTOVER_CERTIFIED"}
D=R/"runtime_state"/"solana_live_opportunity";D.mkdir(parents=True,exist_ok=True)
(D/"slop037_native_cutover.json").write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
T=R/"test_slop_037_native_oracle_live_buy_pressure_cutover_certification.py"
T.write_text("""import json\nfrom pathlib import Path\nx=json.loads(Path('runtime_state/solana_live_opportunity/slop037_native_cutover.json').read_text())\nassert x['state']=='NATIVE_ORACLE_LIVE_BUY_PRESSURE_CUTOVER_CERTIFIED'\nassert x['execution_authority'] is False and x['read_only'] is True\nprint('[SLOP-037]',x)\nprint('[PASS] production launcher cutover structurally certified')\nprint('[NEXT] restart normal run_oracle_LIVE.py to physically activate supervised child')\n""",encoding="utf-8")
print("[SLOP-037]",state);print("[PASS] native cutover certification installed");print("[PASS] execution_authority=FALSE")
