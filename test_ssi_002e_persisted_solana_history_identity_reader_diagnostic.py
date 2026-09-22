
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002e_persisted_solana_history_identity_reader_diagnostic import print_diagnostic
class T(unittest.TestCase):
 def test_repository_diagnostic(self):
  r=print_diagnostic()
  self.assertEqual(len(r["files"]),2)
  self.assertTrue(any(any(x["tokens"] for x in f["lineage"]) for f in r["files"]))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
