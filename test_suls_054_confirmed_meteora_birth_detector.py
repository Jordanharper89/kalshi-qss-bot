import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_054_confirmed_meteora_birth_detector import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_detector(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"transactions_examined":d["transactions_examined"],"birth_count":d["birth_count"]},sort_keys=True))
  if d["transactions_examined"]==0:self.fail("NO_CONFIRMED_TRANSACTIONS_EXAMINED")
  print("[PASS] SULS-054 confirmed Meteora birth detector")
  print("[SCOPE] Zero births is valid when no verified Meteora birth appears in the bounded live window")
if __name__=="__main__":unittest.main()
