import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import FreshOpportunityState
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import admit_and_freeze,FROZEN_THESIS
class T(unittest.TestCase):
 def test_freeze(self):
  s=(FreshOpportunityState("T1","P1","2026-09-17T12:00:00+00:00",1,60,(("order_flow","BUY_PRESSURE"),),"FRESH"),
     FreshOpportunityState("T2","P2","2026-09-17T12:00:00+00:00",1,60,(("order_flow","SELL_PRESSURE"),),"FRESH"))
  x=admit_and_freeze(s); print("[SLOP-003]",x)
  self.assertEqual(len(x),1); self.assertEqual(x[0].state,"PENDING_60S")
  self.assertEqual(x[0].horizon_seconds,60); self.assertEqual(x[0].friction_bps,200)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))
if __name__=="__main__": unittest.main(verbosity=2)
