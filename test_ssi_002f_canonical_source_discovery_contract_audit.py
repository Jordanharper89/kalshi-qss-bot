
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002f_canonical_source_discovery_contract_audit import print_audit
class T(unittest.TestCase):
 def test_contract_audit(self):
  r=print_audit()
  self.assertEqual(len(r["files"]),2);self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
  self.assertTrue(any(f["lineage"] for f in r["files"]))
if __name__=="__main__":unittest.main(verbosity=2)
