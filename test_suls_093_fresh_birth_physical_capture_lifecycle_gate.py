import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_093_fresh_birth_physical_capture_lifecycle_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["production_runtime_fresh"]:
   self.fail("SULS_PRODUCTION_RUNTIME_NOT_FRESH")
  if not d["fresh_birth_physical_certified"]:
   self.fail("NO_FRESH_PROSPECTIVE_BIRTH_CAPTURED_YET")
  if not d["lifecycle_materialization_certified"]:
   self.fail("FRESH_BIRTH_NOT_MATERIALIZED")
  self.assertFalse(d["profitability_learning_ready"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-093 fresh birth physical capture + lifecycle gate")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
