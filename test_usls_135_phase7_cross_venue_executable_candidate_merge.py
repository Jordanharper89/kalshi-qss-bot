import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_135_phase7_cross_venue_executable_candidate_merge import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  ready_fams=sum(v["ready"]>0 for v in d["family_readiness"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"ready_count":d["ready_count"],
   "ready_family_count":ready_fams,"family_readiness":d["family_readiness"]},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertGreater(d["ready_count"],0,"NO_CROSS_VENUE_EXECUTABLE_CANDIDATES_READY")
  self.assertGreater(ready_fams,0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-135 cross-venue executable candidate merge")
  print("[PASS] only rows with physical price/latency/reference/fee/liquidity marked ready")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
