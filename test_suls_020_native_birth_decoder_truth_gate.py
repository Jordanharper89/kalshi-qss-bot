import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_020_native_birth_decoder_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["verified_pool_birth_decoder_ready"])
  print("[PASS] SULS-020 native birth decoder truth gate")
if __name__=="__main__":unittest.main()
