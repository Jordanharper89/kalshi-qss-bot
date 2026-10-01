import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_087_production_activation_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["production_activation_ready"]:self.fail("SULS_PRODUCTION_ACTIVATION_NOT_READY")
  self.assertFalse(d["top_level_launcher_change_required"])
  self.assertFalse(d["production_24x7_active"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-087 production activation readiness gate")
if __name__=="__main__":unittest.main()
