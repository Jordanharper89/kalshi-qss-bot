import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_056_confirmed_fast_lane_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_fast_lane_foundation_ready"]:self.fail("CONFIRMED_FAST_LANE_FOUNDATION_NOT_READY")
  self.assertFalse(d["continuous_confirmed_birth_worker_active"])
  self.assertFalse(d["profitability_learning_ready"])
  print("[PASS] SULS-056 confirmed fast-lane readiness gate")
if __name__=="__main__":unittest.main()
