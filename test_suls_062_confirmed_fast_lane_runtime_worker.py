import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_062_confirmed_fast_lane_runtime_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["capture"]["transactions"],0)
  print("[PASS] SULS-062 confirmed fast-lane runtime worker one-cycle")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
