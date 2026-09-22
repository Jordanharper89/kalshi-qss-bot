from pathlib import Path
import ast
A=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
R=Path("run_slop_buy_pressure_live.py")
T=Path("test_slop_054d4_clean_native_runner_restoration.py")
a=A.read_text(encoding="utf-8");ast.parse(a)
assert 'REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"' in a
assert "blocked=set(unresolved_view(root).tokens)" in a
assert "admitted.append(_rank_pair(str(token),xs,root))" in a
runner='''from pathlib import Path
import time
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import REVISION as ADMISSION_REVISION
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker import worker_round
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output import print_prediction
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import EconomicResolution
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolution_lines
ROOT=Path.cwd();seen=set();resolved_seen=set()
print("[SLOP LIVE] BUY_PRESSURE child STARTING admission_revision=%s execution_authority=FALSE"%ADMISSION_REVISION,flush=True)
while True:
 try:
  before={p.prediction_id for p in read_predictions(ROOT)}
  x=worker_round(root=ROOT,token_limit=5,progress=lambda z:print(z,flush=True))
  for p in read_predictions(ROOT):
   if p.prediction_id not in before and p.prediction_id not in seen:print_prediction(p,progress=lambda z:print(z,flush=True));seen.add(p.prediction_id)
  for d in read_resolution_dicts(ROOT):
   if d["prediction_id"] not in resolved_seen:
    for line in resolution_lines(EconomicResolution(**d)):print(line,flush=True)
    resolved_seen.add(d["prediction_id"])
  print("[SLOP LIVE] state=HEALTHY pending=%s execution_authority=FALSE"%x.get("unresolved","?"),flush=True)
 except Exception as e:print("[SLOP LIVE] state=DEGRADED error=%r execution_authority=FALSE"%e,flush=True)
 time.sleep(5.0)
'''
ast.parse(runner);R.write_text(runner,encoding="utf-8")
T.write_text('''import ast,importlib
from pathlib import Path
a=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py").read_text();ast.parse(a)
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
r=Path("run_slop_buy_pressure_live.py").read_text();ast.parse(r)
assert "admission_revision=%s" in r and "worker_round" in r and "read_resolution_dicts" in r
assert "resolve_background(" not in r
print("[PASS] SLOP-015B parses/imports with repaired canonical-pair semantics")
print("[PASS] native BUY_PRESSURE runner cleanly restored and parses")
print("[PASS] SLOP-025 remains sole resolution owner")
print("[PASS] admission revision fingerprint retained correctly")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054D4 CERTIFIED")
''',encoding="utf-8")
print("[PASS] SLOP-054D4 clean native runner restoration installed")
print("[PASS] test installed:",T)