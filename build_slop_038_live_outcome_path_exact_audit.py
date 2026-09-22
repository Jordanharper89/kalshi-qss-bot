from pathlib import Path
import importlib, inspect, json
ROOT=Path.cwd()
mods=[
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_durable_idempotent_economic_resolution_ledger",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_030_inflight_uniqueness_rotating_universe",
"qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output"]
def sigs(name):
 m=importlib.import_module(name); out={}
 for n,v in vars(m).items():
  if inspect.isfunction(v) and getattr(v,"__module__","")==m.__name__:
   try: out[n]=str(inspect.signature(v))
   except Exception: pass
 return out
report={"schema":"SLOP-038","execution_authority":False,"modules":{}}
for name in mods:
 try: report["modules"][name]={"state":"FOUND","functions":sigs(name)}
 except Exception as e: report["modules"][name]={"state":"ERROR","error":type(e).__name__+":"+str(e)}
runner=ROOT/"run_slop_buy_pressure_live.py"
report["runner_exists"]=runner.exists()
report["runner_source"]=runner.read_text(encoding="utf-8") if runner.exists() else ""
state=ROOT/"runtime_state"/"solana_live_opportunity"; state.mkdir(parents=True,exist_ok=True)
(state/"slop038_exact_outcome_path_audit.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
assert report["runner_exists"]
assert all(v["state"]=="FOUND" for v in report["modules"].values()),report
test=ROOT/"test_slop_038_live_outcome_path_exact_audit.py"
test.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('runtime_state/solana_live_opportunity/slop038_exact_outcome_path_audit.json').read_text())\nassert d['runner_exists'] and d['execution_authority'] is False\nassert all(x['state']=='FOUND' for x in d['modules'].values())\nprint('[PASS] exact outcome-path audit artifact verified')\nprint('[PASS] execution_authority=FALSE')\n",encoding="utf-8")
print("[SLOP-038]",json.dumps({k:v for k,v in report.items() if k!="runner_source"},indent=2))
print("[PASS] exact live outcome path interfaces captured read-only")
print("[PASS] SLOP-038 installed")
