REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
from .slop_012b_exact_fresh_buy_pressure_admission import current_buy_pressure_admission
from .slop_013b_canonical_durable_prediction_ledger_rebuild import persist_predictions
from .slop_014b_pending_token_surveillance_rebuild import pending_surveillance_plan
from .slop_024_unresolved_prediction_surveillance import unresolved_view
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
READ_ONLY=True;EXECUTION_AUTHORITY=False

def _rank_pair(token,candidates,root=None):
 rows=tuple(read_pinned_pool_history(token,root=root,limit=4096));score={}
 for p in candidates:score[p.pair_address]=[0,0.0]
 for r in rows:
  for x in tuple(r.payload.get("pools") or ()):
   a=str(x.get("pair_address") or "")
   if a not in score:continue
   score[a][0]+=1
   try:score[a][1]=max(score[a][1],float(x.get("liquidity_usd") or 0))
   except (TypeError,ValueError):pass
 return max(candidates,key=lambda p:(score[p.pair_address][0],score[p.pair_address][1],p.pair_address))

def lifecycle_pass(active_tokens,root=None,max_age_seconds=20.0,now=None):
 blocked=set(unresolved_view(root).tokens);admitted=[];evaluated=0
 for token in tuple(active_tokens):
  if str(token) in blocked:continue
  x=current_buy_pressure_admission(token,root=root,max_age_seconds=max_age_seconds,now=now);evaluated+=1
  xs=tuple(x["admitted"])
  if xs:admitted.append(_rank_pair(str(token),xs,root))
 if admitted:persisted=persist_predictions(tuple(admitted),root)
 else:
  p0=pending_surveillance_plan(root);persisted={"total":len(p0.prediction_ids),"new":0,"existing":0,"execution_authority":False}
 p=pending_surveillance_plan(root);surveillance=tuple(sorted(set(active_tokens)|set(p.tokens)))
 return {"evaluated":evaluated,"admitted":len(admitted),"persisted":persisted,
 "pending_predictions":len(p.prediction_ids),"surveillance_tokens":surveillance,
 "state":"LIFECYCLE_SINGLE_INFLIGHT_CANONICAL_PAIR","execution_authority":False}
