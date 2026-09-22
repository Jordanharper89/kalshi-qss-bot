from pathlib import Path
from datetime import datetime,timezone
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts

R=Path.cwd()
preds=list(read_predictions(R))
resolved=list(read_resolution_dicts(R))
resolved_ids={str(x.get("prediction_id")) for x in resolved}
now=datetime.now(timezone.utc)

print("="*100)
print(" SLOP-039B PHYSICAL PENDING -> MATURITY -> RESOLUTION DIAGNOSTIC")
print("="*100)
print("[PREDICTIONS]",len(preds))
print("[RESOLUTIONS]",len(resolved))

pending=[]
for p in preds:
    if p.prediction_id in resolved_ids:
        continue
    try:
        frozen=datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))
        age=(now-frozen).total_seconds()
    except Exception as e:
        print("[BAD FROZEN TIME]",p.prediction_id,repr(e))
        continue
    pending.append((age,p))

print("[UNRESOLVED]",len(pending))
for age,p in sorted(pending,reverse=True)[:25]:
    print("\n[PREDICTION]",p.prediction_id)
    print(" token=",p.token_address)
    print(" pair=",p.pair_address)
    print(" age_seconds=",round(age,3))
    print(" frozen_at=",p.frozen_at)
    try:
        path=materialize_frozen_prediction_path(p,R)
        print(" path=",repr(path))
        print(" maturity_state=","PATH_READY" if path is not None else "NO_EXACT_MATURITY_PATH")
    except Exception as e:
        print(" maturity_state=ERROR")
        print(" error_type=",type(e).__name__)
        print(" error=",repr(e))

print("\n[PASS] diagnostic completed read-only")
print("[PASS] execution_authority=FALSE")