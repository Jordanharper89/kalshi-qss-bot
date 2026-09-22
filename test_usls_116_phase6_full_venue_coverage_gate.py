import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_116_phase6_full_venue_coverage_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("certified_family_count","decoder_covered_count",
   "path_covered_count","missing_decoder_families","missing_path_families",
   "full_venue_path_coverage","next_boundary")},sort_keys=True))
  self.assertEqual(d["decoder_covered_count"],d["certified_family_count"],"CERTIFIED_DECODER_REGISTRY_INCOMPLETE")
  self.assertEqual(d["path_covered_count"],d["certified_family_count"],"CERTIFIED_VENUE_PRICE_PATH_COVERAGE_INCOMPLETE")
  self.assertTrue(d["full_venue_path_coverage"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-116 Phase 6 full venue coverage gate")
  print("[PASS] every Phase-4-certified venue has universal continuous price-path coverage")
  print("[NEXT] PHASE6_FINAL_CERTIFICATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
