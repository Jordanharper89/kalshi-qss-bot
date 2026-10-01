import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_090_production_activation_preflight import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["preflight_ready"]:self.fail("PRODUCTION_ACTIVATION_PREFLIGHT_NOT_READY")
  self.assertFalse(d["duplicate_suls_child"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-090 production activation preflight")
if __name__=="__main__":unittest.main()
