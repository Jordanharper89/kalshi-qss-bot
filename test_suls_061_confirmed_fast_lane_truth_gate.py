import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_061_confirmed_fast_lane_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_fast_lane_worker_ready"]:self.fail("CONFIRMED_FAST_LANE_WORKER_NOT_READY")
  self.assertFalse(d["continuous_runtime_active"]);self.assertFalse(d["profitability_learning_ready"])
  print("[PASS] SULS-061 confirmed fast-lane truth gate")
if __name__=="__main__":unittest.main()
