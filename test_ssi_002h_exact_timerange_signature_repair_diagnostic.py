
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002h_exact_timerange_signature_repair_diagnostic import diagnose
class T(unittest.TestCase):
 def test_signature(self):
  r=diagnose()
  self.assertIn("by_observed_time_range",str(__import__("qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract",fromlist=["CanonicalPersistenceQueryRequest"]).CanonicalPersistenceQueryRequest.by_observed_time_range))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
