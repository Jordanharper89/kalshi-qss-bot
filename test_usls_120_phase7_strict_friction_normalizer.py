import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_120_phase7_strict_friction_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],
   "family_row_counts":d["family_row_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0,"NO_PHASE7_NORMALIZED_ROWS")
  self.assertEqual(len(d["family_row_counts"]),14,"NOT_ALL_14_CERTIFIED_FAMILIES_PRESENT")
  self.assertFalse(d["missing_values_are_zero"])
  self.assertEqual(d["friction_unknown_policy"],"RETAIN_NULL_NOT_ZERO")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-120 strict friction normalizer")
  print("[PASS] all 14 venue families normalized; missing friction never fabricated as zero")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
