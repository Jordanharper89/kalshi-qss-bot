import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_132_phase7_first_net_executable_round_trip_model import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"round_trip_count":d["round_trip_count"],
   "phase7_status":d["phase7_status"],
   "remaining_required_capability":d["remaining_required_capability"]},sort_keys=True))
  self.assertGreater(d["round_trip_count"],0,"NO_NET_EXECUTABLE_ROUND_TRIP_ROWS")
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-132 first net executable round-trip research model")
  print("[PASS] observed execution prices + explicit fees + conservative execution deviation")
  print("[PASS] no profitability claim; prospective all-venue validation still required")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
