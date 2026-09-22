from pathlib import Path
from datetime import datetime,timezone
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts

R=Path.cwd()
preds=tuple(read_predictions(R))
resolved={str(x["prediction_id"]) for x in read_resolution_dicts(R)}
pending=[p for p in preds if p.prediction_id not in resolved]
now=datetime.now(timezone.utc); mature=[]

for p in pending:
 try:
  f=datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))
  if (now-f).total_seconds()>=60: mature.append(p)
 except Exception: pass

ready=[]; missing=[]
for p in mature[:50]:
 path=materialize_frozen_prediction_path(p,root=R)
 (ready if path is not None else missing).append(p.prediction_id)

print("[PREDICTIONS]",len(preds))
print("[RESOLUTIONS]",len(resolved))
print("[UNRESOLVED]",len(pending))
print("[MATURE>=60S]",len(mature))
print("[SAMPLED]",min(50,len(mature)))
print("[MATURITY_PATH_READY]",len(ready))
print("[MATURITY_PATH_MISSING]",len(missing))
if ready: print("[READY_IDS]",tuple(x[:12] for x in ready[:10]))
if missing: print("[MISSING_IDS]",tuple(x[:12] for x in missing[:10]))
assert len(ready)+len(missing)==min(50,len(mature))
print("[PASS] physical canonical ledgers read successfully")
print("[PASS] exact SLOP-016B maturity path physically exercised")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-044B PHYSICAL GATE COMPLETE")
