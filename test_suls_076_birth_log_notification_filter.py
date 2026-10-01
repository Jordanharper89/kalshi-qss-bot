import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_076_birth_log_notification_filter import write,is_birth,DBC,DAMM
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_filter(self):
  fixture=["Program "+DBC+" invoke [1]","Program "+DAMM+" invoke [2]","Program log: Create Pool","Program log: Instruction: InitializePoolWithDynamicConfig"]
  self.assertTrue(is_birth(fixture))
  p,d=write(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="births"},sort_keys=True))
  print("[PASS] SULS-076 birth log notification filter")
  print("[SCOPE] Zero physical birth candidates is valid during a short probe window")
if __name__=="__main__":unittest.main()
