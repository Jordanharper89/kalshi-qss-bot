
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_001e_solana_profitability_input_lineage_audit import render
class T(unittest.TestCase):
 def test_physical_repo_lineage(self):
  r=render()
  self.assertGreaterEqual(len(r["files"]),2)
  self.assertTrue(any("oad_314" in x["path"] for x in r["files"]))
  self.assertFalse(r["execution_authority"])
  self.assertTrue(r["read_only"])
if __name__=="__main__": unittest.main(verbosity=2)
