import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_040_native_lifecycle_activation_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["physical_native_vault_readback"] or not d["prospective_schedule_ready"]:
   self.fail("NATIVE_LIFECYCLE_FOUNDATION_NOT_READY")
  self.assertFalse(d["continuous_native_lifecycle_active"])
  self.assertFalse(d["profitable_edge_claimed"])
  print("[PASS] SULS-040 native lifecycle activation truth gate")
if __name__=="__main__":unittest.main()
