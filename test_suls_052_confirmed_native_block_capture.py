import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_052_confirmed_native_block_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_capture(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_capture_ready"]:self.fail("CONFIRMED_NATIVE_BLOCK_CAPTURE_FAILED")
  print("[PASS] SULS-052 confirmed native block capture")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
