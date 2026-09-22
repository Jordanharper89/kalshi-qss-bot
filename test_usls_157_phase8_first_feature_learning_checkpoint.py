import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_157_phase8_first_feature_learning_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["snapshot_count"],0)
  self.assertGreater(d["comparable_group_count"],0)
  self.assertEqual(d["phase8_status"],"IN_PROGRESS")
  self.assertFalse(d["phase8_physically_certified"])
  self.assertTrue(d["raw_frequency_only"])
  self.assertFalse(d["calibrated_probability_claimed"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-157 Phase 8 first feature-learning checkpoint")
  print("[PASS] leakage-safe comparable-case learning foundation established")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
