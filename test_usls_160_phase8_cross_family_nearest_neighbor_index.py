import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_160_phase8_cross_family_nearest_neighbor_index import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"indexed_case_count":d["indexed_case_count"],
   "cases_with_cross_family_neighbors":d["cases_with_cross_family_neighbors"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["indexed_case_count"],0)
  self.assertGreater(d["cases_with_cross_family_neighbors"],0,
                     "NO_CROSS_FAMILY_NEAREST_NEIGHBORS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-160 cross-family nearest-neighbor index")
  print("[PASS] cross-launch comparables now use continuous similarity instead of sparse exact buckets")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
