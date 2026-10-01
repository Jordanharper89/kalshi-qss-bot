import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_025_native_birth_verification_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["exact_native_birth_verified"]:self.fail("EXACT_NATIVE_BIRTH_NOT_VERIFIED")
  print("[PASS] SULS-025 native birth verification truth gate")
if __name__=="__main__":unittest.main()
