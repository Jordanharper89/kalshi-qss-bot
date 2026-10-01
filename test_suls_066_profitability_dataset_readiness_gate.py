import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_066_profitability_dataset_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["fast_lane_under_5s"] or not d["slot_continuity_monotonic"]:self.fail("FAST_LANE_FOUNDATION_NOT_READY")
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-066 profitability dataset readiness gate")
if __name__=="__main__":unittest.main()
