from pathlib import Path
import time
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import REVISION as ADMISSION_REVISION
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker import worker_round
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output import print_prediction
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import EconomicResolution
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolution_lines
from qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation import RegisteredChildObservation
ROOT=Path.cwd();seen=set();resolved_seen=set()
opportunity_observer=RegisteredChildObservation(ROOT)
print("[SLOP LIVE] BUY_PRESSURE child STARTING admission_revision=%s execution_authority=FALSE"%ADMISSION_REVISION,flush=True)
while True:
 try:
  before={p.prediction_id for p in read_predictions(ROOT)}
  observation_prepared=False
  try:
   opportunity_observer.prepare();observation_prepared=True
  except Exception as observation_error:
   opportunity_observer.failure(observation_error)
   print("[OOI LIVE] state=DEGRADED error=%r execution_authority=FALSE"%observation_error,flush=True)
  x=worker_round(root=ROOT,token_limit=5,progress=lambda z:print(z,flush=True))
  if observation_prepared:
   try:
    opportunity_status=opportunity_observer.complete(x)
    opportunity_report=opportunity_status["observation"]
    print("[OOI LIVE] fresh=%s accepted=%s held=%s active=%s execution_authority=FALSE"%tuple(opportunity_report[k] for k in ("fresh_candidates","accepted","held","active_owned_count")),flush=True)
   except Exception as observation_error:
    opportunity_observer.failure(observation_error)
    print("[OOI LIVE] state=DEGRADED error=%r execution_authority=FALSE"%observation_error,flush=True)
  for p in read_predictions(ROOT):
   if p.prediction_id not in before and p.prediction_id not in seen:print_prediction(p,progress=lambda z:print(z,flush=True));seen.add(p.prediction_id)
  for d in read_resolution_dicts(ROOT):
   if d["prediction_id"] not in resolved_seen:
    for line in resolution_lines(EconomicResolution(**d)):print(line,flush=True)
    resolved_seen.add(d["prediction_id"])
  print("[SLOP LIVE] state=HEALTHY pending=%s execution_authority=FALSE"%x.get("unresolved","?"),flush=True)
 except Exception as e:
  opportunity_observer.failure(e)
  print("[SLOP LIVE] state=DEGRADED error=%r execution_authority=FALSE"%e,flush=True)
 time.sleep(5.0)
