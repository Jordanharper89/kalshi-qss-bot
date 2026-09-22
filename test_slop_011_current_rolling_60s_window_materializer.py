import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011_current_rolling_60s_window_materializer import current_fresh_60s_states
class T(unittest.TestCase):
 def test_current(self):
  now=datetime.now(timezone.utc);w=SimpleNamespace(window_seconds=60,state="WINDOW_READY",last_observed_at=now.isoformat(),conditions=(("P",(("order_flow","BUY_PRESSURE"),),"READY"),))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011_current_rolling_60s_window_materializer.read_pinned_pool_history",return_value=(1,2)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011_current_rolling_60s_window_materializer.build_multi_horizon_solana_states",return_value=(w,)):
   x=current_fresh_60s_states("T",now=now)
  print("[SLOP-011]",x);self.assertEqual(len(x["fresh_states"]),1);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
