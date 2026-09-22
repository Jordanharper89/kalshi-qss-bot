import unittest
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
