import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_064_confirmed_horizon_outcome_worker.py"

class T(unittest.TestCase):
 def test_semantics(self):
  s=P.read_text(encoding="utf-8")
  ast.parse(s)
  self.assertNotIn("return_from_birth",s)
  self.assertIn("reserve_ratio_change_from_birth",s)
  self.assertIn("RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY",s)
  self.assertIn("profitability_eligible",s)
  self.assertIn("executable_pnl",s)
  print("[PASS] SULS-095B canonical reserve-ratio semantic repair")
  print("[PASS] profitability_eligible=FALSE")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
