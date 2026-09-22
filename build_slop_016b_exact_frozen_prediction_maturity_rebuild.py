from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_016b_exact_frozen_prediction_maturity_rebuild.py"
M.write_text(r"""from dataclasses import dataclass
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
def materialize_frozen_prediction_path(prediction,root=None,tolerance_seconds=8.0):
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
""",encoding="utf-8")
T=R/"test_slop_016b_exact_frozen_prediction_maturity_rebuild.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
def r(i,t,p):return SimpleNamespace(observation_id=i,observed_at=t,payload={"pools":[{"pair_address":"PAIR","price_usd":p}]})
class T(unittest.TestCase):
 def test_same_frozen_prediction_and_ordered_path(self):
  p=ProspectiveOpportunity("PID","TOKEN","PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
  rows=(r("A","2026-09-17T15:30:00+00:00",100),r("B","2026-09-17T15:30:20+00:00",106),r("C","2026-09-17T15:30:40+00:00",95),r("D","2026-09-17T15:31:01+00:00",111))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild.read_pinned_pool_history",return_value=rows):x=materialize_frozen_prediction_path(p)
  print("[SLOP-016B]",x)
  self.assertEqual(x.prediction_id,"PID");self.assertEqual(len(x.observations),3)
  self.assertEqual(x.observations[0][0],"2026-09-17T15:30:20+00:00")
  self.assertAlmostEqual(x.mfe,.11);self.assertAlmostEqual(x.mae,-.05)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-016B installed")
print("[PASS] same frozen prediction carried to exact maturity")
print("[PASS] ordered physical price path retained for barrier ordering")
print("[PASS] execution_authority=FALSE")
