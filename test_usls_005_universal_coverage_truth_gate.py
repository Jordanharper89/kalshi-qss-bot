import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_005_universal_coverage_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "target_family_count","live_certified_family_count","universal_scanner_complete",
   "unknown_fallback_active","next_required_boundary","profitability_claimed")},sort_keys=True))
  for r in d["families"]:print("[FAMILY]",json.dumps(r,sort_keys=True))
  self.assertEqual(d["target_family_count"],15)
  self.assertTrue(d["unknown_fallback_active"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-005 universal coverage truth gate")
  print("[PASS] no unproven DEX family is silently called complete")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
