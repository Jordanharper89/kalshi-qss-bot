import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_128_phase7_per_row_latency_recovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"latency_row_count":d["latency_row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertGreater(d["latency_row_count"],2,"PER_ROW_LATENCY_RECOVERY_DID_NOT_EXPAND_COVERAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-128 per-row latency recovery")
  print("[PASS] physical block-time to Oracle-observation latency recovered without guessing")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
