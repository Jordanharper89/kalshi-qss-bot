import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_048_finalized_launch_role_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["finalized_role"],("PRIMARY_LAUNCH_TRIGGER","CONFIRMATION_AND_OUTCOME_TRUTH"))
  print("[PASS] SULS-048 finalized launch-role truth gate")
if __name__=="__main__":unittest.main()
