
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002m_consolidated_physical_history_to_price_paths_closeout import closeout
class T(unittest.TestCase):
 def test_consolidated_physical_closeout(self):
  r=closeout()
  self.assertGreaterEqual(r["history_rows"],2);self.assertGreater(r["cases"],0);self.assertGreater(r["paths"],0)
  self.assertTrue(r["pairs"]);self.assertTrue(r["sample_lineage"]);self.assertTrue(any(r["by_horizon"].values()))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
