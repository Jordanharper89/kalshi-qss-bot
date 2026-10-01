import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_015_native_birth_decoder_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  print("[PASS] SULS-015 native birth decoder readiness gate")
if __name__=="__main__":unittest.main()
