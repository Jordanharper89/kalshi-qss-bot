import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_semantics(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="queue"},sort_keys=True))
  self.assertFalse(d["age_1s_birth_claim_allowed"])
  print("[PASS] SULS-063 signal-relative horizon semantics")
if __name__=="__main__":unittest.main()
