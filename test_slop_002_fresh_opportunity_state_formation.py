import unittest
from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import form_fresh_opportunity_states
class T(unittest.TestCase):
 def test_freshness(self):
  now=datetime.now(timezone.utc); c=SimpleNamespace(token_address="T",windows=(
   SimpleNamespace(window_seconds=60,state="WINDOW_READY",last_observed_at=(now-timedelta(seconds=3)).isoformat(),conditions=(("P",(("order_flow","BUY_PRESSURE"),),"READY"),)),
   SimpleNamespace(window_seconds=15,state="WINDOW_READY",last_observed_at=now.isoformat(),conditions=()),))
  x=form_fresh_opportunity_states(c,now=now,max_age_seconds=20)
  print("[SLOP-002]",x)
  self.assertEqual(len(x),1); self.assertEqual(x[0].state,"FRESH"); self.assertFalse(x[0].execution_authority)
if __name__=="__main__": unittest.main(verbosity=2)
