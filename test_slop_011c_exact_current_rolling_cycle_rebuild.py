import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild import current_fresh_60s_states

class T(unittest.TestCase):
 def test_exact_slop002_contract(self):
  now=datetime.now(timezone.utc)
  w=SimpleNamespace(
   window_seconds=60,
   state="WINDOW_READY",
   last_observed_at=now.isoformat(),
   conditions=(
    ("PAIR",(("order_flow","BUY_PRESSURE"),),"CONDITIONS_READY"),
   )
  )
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild.read_pinned_pool_history",return_value=(1,2)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild.build_multi_horizon_solana_states",return_value=(w,)):
   x=current_fresh_60s_states("TOKEN",now=now)

  print("[SLOP-011C]",x)
  self.assertEqual(x["token_address"],"TOKEN")
  self.assertEqual(x["windows"],1)
  self.assertEqual(len(x["states"]),1)
  self.assertEqual(len(x["fresh_states"]),1)

  s=x["fresh_states"][0]
  self.assertEqual(s.token_address,"TOKEN")
  self.assertEqual(s.pair_address,"PAIR")
  self.assertEqual(s.window_seconds,60)
  self.assertEqual(s.state,"FRESH")
  self.assertIn(("order_flow","BUY_PRESSURE"),s.conditions)
  self.assertFalse(s.execution_authority)
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 unittest.main(verbosity=2)
