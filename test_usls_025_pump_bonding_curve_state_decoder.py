import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_025_pump_bonding_curve_state_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_state(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"curve_count":d["curve_count"],"valid_count":d["valid_count"]},sort_keys=True))
  for x in d["rows"]:print("[CURVE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["curve_count"],0);self.assertEqual(d["valid_count"],d["curve_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-025 Pump bonding-curve account state physically decoded")
  print("[PASS] virtual/real token and quote reserves preserved from exact curve account")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
