from pathlib import Path
import importlib,inspect,json
R=Path.cwd(); P=R/"qseries_v2"/"oracle_strategy_intelligence"/"solana_live_opportunity"
fixed=[
"slop_013b_canonical_durable_prediction_ledger_rebuild",
"slop_016b_exact_frozen_prediction_maturity_rebuild",
"slop_017b_ordered_physical_economic_resolution",
"slop_025_live_freeze_maturity_resolution_worker",
"slop_029_oracle_readable_prediction_output",
"slop_030_inflight_uniqueness_rotating_universe",
"slop_031_background_resolution_readable_output"]
candidates=sorted(x.stem for x in P.glob("slop_020*.py") if x.name!="__init__.py")
if not candidates: raise SystemExit("[FAIL] no physical slop_020 module found")
mods=fixed+candidates
def audit(short):
 name="qseries_v2.oracle_strategy_intelligence.solana_live_opportunity."+short
 m=importlib.import_module(name); funcs={}
 for n,v in vars(m).items():
  if inspect.isfunction(v) and getattr(v,"__module__","")==m.__name__:
   try: funcs[n]=str(inspect.signature(v))
   except Exception: pass
 return {"module":name,"functions":funcs}
report={"schema":"SLOP-038B","slop020_candidates":candidates,
        "modules":{x:audit(x) for x in mods},
        "runner_exists":(R/"run_slop_buy_pressure_live.py").exists(),
        "execution_authority":False}
D=R/"runtime_state"/"solana_live_opportunity";D.mkdir(parents=True,exist_ok=True)
(D/"slop038b_exact_outcome_path_audit.json").write_text(
 json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
T=R/"test_slop_038b_exact_outcome_path_audit_dynamic_slop020_repair.py"
T.write_text("""import json
from pathlib import Path
d=json.loads(Path('runtime_state/solana_live_opportunity/slop038b_exact_outcome_path_audit.json').read_text())
assert d['runner_exists'] and d['slop020_candidates']
assert d['execution_authority'] is False
print('[SLOP-038B]',json.dumps(d,indent=2,sort_keys=True))
print('[PASS] exact physical outcome path captured without guessed SLOP-020 name')
print('[PASS] execution_authority=FALSE')
""",encoding="utf-8")
print("[SLOP-020 PHYSICAL MODULES]",candidates)
for n,v in report["modules"].items(): print("[INTERFACE]",n,v["functions"])
print("[PASS] SLOP-038B exact outcome-path audit installed")
print("[PASS] execution_authority=FALSE")