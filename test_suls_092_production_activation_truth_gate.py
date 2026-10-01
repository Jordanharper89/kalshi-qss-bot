import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_092_production_activation_truth_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["event_driven_solana_birth_surveillance_active"]:
   self.fail("SULS_PRODUCTION_NOT_ACTIVE")
  self.assertTrue(d["production_24x7_active"])
  self.assertFalse(d["fresh_birth_physical_certified"])
  self.assertFalse(d["profitability_learning_ready"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-092 production activation truth gate")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
