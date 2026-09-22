import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_153_phase8_cross_launch_feature_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(d["phase"],8)
  self.assertEqual(d["capability"],"CROSS_LAUNCH_FEATURE_LEARNING")
  self.assertEqual(d["learning_rules"]["future_leakage"],"FORBIDDEN")
  self.assertTrue(d["learning_rules"]["raw_frequency_is_not_calibrated_probability"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-153 Phase 8 cross-launch feature contract")
  print("[PASS] leakage-safe feature/outcome semantics frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
