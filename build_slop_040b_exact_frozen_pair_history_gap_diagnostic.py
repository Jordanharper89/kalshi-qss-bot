from pathlib import Path
from datetime import datetime,timezone
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_314_solana_forward_outcome_attribution import _price_for_pair

R=Path.cwd()
now=datetime.now(timezone.utc)
preds=list(read_predictions(R))

eligible=[]
for p in preds:
    try:
        f=datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))
        age=(now-f).total_seconds()
        if age>=60:
            eligible.append((age,p,f))
    except Exception:
        pass

eligible.sort(key=lambda x:x[0],reverse=True)

print("="*110)
print(" SLOP-040B EXACT FROZEN PAIR HISTORY GAP DIAGNOSTIC")
print("="*110)
print("[MATURE PREDICTIONS]",len(eligible))

for age,p,frozen in eligible[:15]:
    rows=list(read_pinned_pool_history(
        token_address=p.token_address,
        root=R,
        limit=512
    ))

    after=[]
    pair_after=[]
    priced_after=[]

    for row in rows:
        raw=(row.get("observed_at") or
             row.get("timestamp") or
             row.get("captured_at"))
        if not raw:
            continue

        try:
            t=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        except Exception:
            continue

        if t <= frozen:
            continue

        after.append(row)

        pair=(row.get("pair_address") or
              row.get("pair") or
              row.get("pool_address"))

        if str(pair)==str(p.pair_address):
            pair_after.append(row)

        try:
            price=_price_for_pair(row,p.pair_address)
        except Exception:
            price=None

        if price is not None:
            priced_after.append((t,price))

    print("\n[PREDICTION]",p.prediction_id)
    print(" token=",p.token_address)
    print(" frozen_pair=",p.pair_address)
    print(" age_seconds=",round(age,3))
    print(" history_rows=",len(rows))
    print(" post_freeze_token_rows=",len(after))
    print(" post_freeze_exact_pair_rows=",len(pair_after))
    print(" post_freeze_priced_pair_rows=",len(priced_after))

    if priced_after:
        print(" first_future_price=",priced_after[0])
        print(" last_future_price=",priced_after[-1])
        print(" state=EXACT_PAIR_PRICE_HISTORY_EXISTS")
    elif after:
        print(" state=TOKEN_HISTORY_EXISTS_BUT_FROZEN_PAIR_MISSING")
    else:
        print(" state=POST_FREEZE_TOKEN_HISTORY_MISSING")

print("\n[PASS] read-only frozen-pair lineage diagnostic complete")
print("[PASS] execution_authority=FALSE")