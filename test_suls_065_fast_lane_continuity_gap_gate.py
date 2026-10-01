import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_065_fast_lane_continuity_gap_gate import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=run(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["monotonic"]:self.fail("FAST_LANE_SLOT_ROLLBACK")
  print("[PASS] SULS-065 fast-lane continuity/gap gate")
if __name__=="__main__":unittest.main()
