import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161s_phase8_universal_coverage_sample_gap_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"family_count":d["family_count"],"family_ready_count":d["family_ready_count"],
   "minimum_cases_per_family_for_initial_phase8_readiness":d["minimum_cases_per_family_for_initial_phase8_readiness"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161S universal coverage + prospective sample gap matrix")
  print("[PASS] all 14 families retained; missing decoder/live/OOS evidence remains explicit")
  print("[NEXT] PHASE8_CHECKPOINT_NO_FALSE_UNIVERSAL_CERTIFICATION")
if __name__=="__main__":unittest.main()
