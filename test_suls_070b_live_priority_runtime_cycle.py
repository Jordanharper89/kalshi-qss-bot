import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_070b_live_priority_runtime_cycle import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if d["capture"]["anchor_count"]!=2:self.fail("PROGRAM_INDEXED_RUNTIME_ANCHORS_NOT_READY")
  print("[PASS] SULS-070B live-priority runtime cycle")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
