from dataclasses import dataclass
from datetime import datetime,timedelta
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair
READ_ONLY=True;EXECUTION_AUTHORITY=False
def _dt(v):return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class FrozenPredictionPath:
 prediction_id:str;token_address:str;pair_address:str;frozen_at:str;anchor_at:str;anchor_price:float
 outcome_at:str;outcome_price:float;observations:tuple;return_fraction:float;mfe:float;mae:float
 evidence_observation_ids:tuple;execution_authority:bool=False
def materialize_frozen_prediction_path(prediction,root=None,tolerance_seconds=30.0):
 rows=tuple(sorted(read_pinned_pool_history(prediction.token_address,root=root,limit=4096),key=lambda r:_dt(r.observed_at)))
 at=_dt(prediction.frozen_at)
 anchors=[r for r in rows if _dt(r.observed_at)<=at and _price_for_pair(r,prediction.pair_address) is not None]
 if not anchors:return None
 anchor=anchors[-1];ap=float(_price_for_pair(anchor,prediction.pair_address))
 target_at=at+timedelta(seconds=int(prediction.horizon_seconds))
 eligible=[r for r in rows if _dt(r.observed_at)>at and _dt(r.observed_at)<=target_at+timedelta(seconds=float(tolerance_seconds)) and _price_for_pair(r,prediction.pair_address) is not None]
 terminal=[r for r in eligible if _dt(r.observed_at)>=target_at]
 if not terminal:return None
 end=terminal[0];path=[r for r in eligible if _dt(r.observed_at)<=_dt(end.observed_at)]
 obs=tuple((str(r.observed_at),float(_price_for_pair(r,prediction.pair_address)),str(r.observation_id)) for r in path)
 rets=tuple(px/ap-1.0 for _,px,_ in obs);op=obs[-1][1]
 return FrozenPredictionPath(prediction.prediction_id,prediction.token_address,prediction.pair_address,
  prediction.frozen_at,str(anchor.observed_at),ap,obs[-1][0],op,obs,op/ap-1.0,max(rets),min(rets),
  tuple([str(anchor.observation_id)]+[oid for _,_,oid in obs]),False)
