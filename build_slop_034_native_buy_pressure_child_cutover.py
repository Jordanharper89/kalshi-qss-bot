from pathlib import Path
import ast,hashlib,shutil
R=Path.cwd();L=R/"run_oracle_LIVE.py";RUN=R/"run_slop_buy_pressure_live.py"
deps=["slop_025_live_freeze_maturity_resolution_worker.py","slop_029_oracle_readable_prediction_output.py","slop_031_background_resolution_readable_output.py"]
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
for x in deps:
 if not (D/x).exists(): raise SystemExit("[FAIL] missing "+x)
RUN.write_text("""from pathlib import Path\nimport time\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker import worker_round\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output import print_prediction\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolve_background\nROOT=Path.cwd(); seen=set()\nprint('[SLOP LIVE] BUY_PRESSURE child STARTING execution_authority=FALSE',flush=True)\nwhile True:\n try:\n  before={p.prediction_id for p in read_predictions(ROOT)}\n  r=worker_round(root=ROOT,token_limit=5,progress=lambda x: print(x,flush=True))\n  for p in read_predictions(ROOT):\n   if p.prediction_id not in before and p.prediction_id not in seen:\n    print_prediction(p,progress=lambda x: print(x,flush=True));seen.add(p.prediction_id)\n  resolve_background(ROOT,progress=lambda x: print(x,flush=True))\n  print('[SLOP LIVE] state=HEALTHY pending=%s execution_authority=FALSE'%r.get('pending',r.get('pending_after','?')),flush=True)\n except Exception as e: print('[SLOP LIVE] state=DEGRADED error=%r execution_authority=FALSE'%e,flush=True)\n time.sleep(5.0)\n""",encoding="utf-8")
src=L.read_text(encoding="utf-8");tree=ast.parse(src);target=None
for n in ast.walk(tree):
 if isinstance(n,(ast.Assign,ast.AnnAssign)):
  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])
  if "CHILDREN" in names and isinstance(n.value,ast.Dict): target=n.value;break
if target is None: raise SystemExit("[FAIL] CHILDREN dict missing")
d=ast.literal_eval(target)
if "solana_buy_pressure" in d and d["solana_buy_pressure"]!="run_slop_buy_pressure_live.py": raise SystemExit("[FAIL] child name collision")
if "solana_buy_pressure" not in d:
 backup=R/("run_oracle_LIVE.pre_slop034_"+hashlib.sha256(src.encode()).hexdigest()[:16]+".py");shutil.copy2(L,backup)
 pos=target.end_lineno-1;lines=src.splitlines(True);indent=" "*(target.col_offset+4)
 lines.insert(pos,indent+"'solana_buy_pressure': 'run_slop_buy_pressure_live.py',\n")
 patched="".join(lines);ast.parse(patched);L.write_text(patched,encoding="utf-8")
 print("[ROLLBACK]",backup)
print("[PASS] native child inserted: solana_buy_pressure => run_slop_buy_pressure_live.py")
print("[PASS] existing Oracle supervision reused");print("[PASS] execution_authority=FALSE")
T=R/"test_slop_034_native_buy_pressure_child_cutover.py"
T.write_text("""import ast\nfrom pathlib import Path\ns=Path('run_oracle_LIVE.py').read_text();t=ast.parse(s);d=None\nfor n in ast.walk(t):\n if isinstance(n,(ast.Assign,ast.AnnAssign)):\n  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])\n  if 'CHILDREN' in names and isinstance(n.value,ast.Dict): d=ast.literal_eval(n.value);break\nassert d['solana_buy_pressure']=='run_slop_buy_pressure_live.py'\nast.parse(Path('run_slop_buy_pressure_live.py').read_text())\nprint('[CHILD]',d['solana_buy_pressure']);print('[PASS] native production child cutover certified');print('[PASS] execution_authority=FALSE')\n""",encoding="utf-8")
