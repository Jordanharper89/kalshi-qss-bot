from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import unresolved_view
cut=datetime.fromisoformat(open("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt").read().strip().replace("Z","+00:00"))
ps=[p for p in read_predictions() if datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))>=cut]
rs={r["prediction_id"]:r for r in read_resolution_dicts()}
u=unresolved_view();by={}
for p in ps:by.setdefault(p.token_address,[]).append(p)
dup={t:sorted(x,key=lambda p:str(p.frozen_at)) for t,x in by.items() if len(x)>1}
print("[CLEAN]",len(ps),"[DUPLICATE_TOKENS]",len(dup))
assert dup,"NO_DUPLICATE_AVAILABLE_FOR_DIAGNOSTIC"
for token,xs in dup.items():
 print("[TOKEN]",token)
 for p in xs:
  ft=datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))
  print("[PRED]",p.prediction_id,"pair=",p.pair_address,"frozen=",p.frozen_at,
        "resolved=",p.prediction_id in rs,"currently_unresolved=",p.prediction_id in set(u.prediction_ids))
 for a,b in zip(xs,xs[1:]):
  ta=datetime.fromisoformat(str(a.frozen_at).replace("Z","+00:00"))
  tb=datetime.fromisoformat(str(b.frozen_at).replace("Z","+00:00"))
  delta=(tb-ta).total_seconds()
  print("[ADMISSION_DELTA_SECONDS]",delta)
  print("[OVERLAPPED_60S_INFLIGHT]",delta<60.0)
print("[UNRESOLVED_TOKENS_NOW]",tuple(u.tokens))
print("[PASS] SLOP-054B duplicate inflight physical diagnostic complete")
print("[PASS] no production mutation; execution_authority=FALSE")
