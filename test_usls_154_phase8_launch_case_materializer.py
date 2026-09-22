import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_154_phase8_launch_case_materializer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"case_count":d["case_count"],
   "family_case_counts":d["family_case_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0,"NO_PHASE8_LAUNCH_CASES")
  self.assertEqual(len(d["family_case_counts"]),14)
  self.assertEqual(d["case_semantics"],"OBSERVATIONAL_CROSS_LAUNCH_CASES_NOT_EXECUTABLE_PNL")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-154 Phase 8 launch-case materializer")
  print("[PASS] all 14 certified venue families represented as observational learning cases")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
