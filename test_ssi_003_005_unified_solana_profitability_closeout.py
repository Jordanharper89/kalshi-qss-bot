
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_003_005_unified_solana_profitability_closeout import discover
class T(unittest.TestCase):
 def test_unified_profitability_closeout(self):
  r=discover()
  self.assertGreater(r["history_rows"],10);self.assertGreater(r["examples"],0)
  self.assertGreater(r["train"],0);self.assertGreater(r["oos"],0);self.assertGreater(r["candidates_tested"],0)
  self.assertIn(r["profitability_state"],("OOS_POSITIVE_NET_EXPECTANCY_FOUND","NO_CERTIFIED_PROFITABLE_THESIS_YET"))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
