import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import FreshOpportunityState
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_012b_exact_fresh_buy_pressure_admission import current_buy_pressure_admission

class T(unittest.TestCase):
 def test_exact_prospective_freeze(self):
  s=FreshOpportunityState("TOKEN","PAIR","2026-09-17T15:30:00+00:00",1.0,60,(("order_flow","BUY_PRESSURE"),),"FRESH",False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_012b_exact_fresh_buy_pressure_admission.current_fresh_60s_states",return_value={"fresh_states":(s,)}):
   x=current_buy_pressure_admission("TOKEN")
  print("[SLOP-012B]",x)
  self.assertEqual(x["admitted_count"],1)
  p=x["admitted"][0]
  self.assertEqual(p.horizon_seconds,60)
  self.assertEqual(p.target,0.10)
  self.assertEqual(p.stop,0.05)
  self.assertEqual(p.friction_bps,200)
  self.assertEqual(p.state,"PENDING_60S")
  self.assertEqual(p.frozen_at,s.observed_at)
  self.assertFalse(p.execution_authority)
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 unittest.main(verbosity=2)
