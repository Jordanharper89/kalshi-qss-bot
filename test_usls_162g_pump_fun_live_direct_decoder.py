import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162g_pump_fun_live_direct_decoder import contract
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  d=contract(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["market_role_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162G Pump.fun live direct decoder contract")
  print("[NEXT] PUMP_FUN_STRICT_LIVE_ECONOMICS_CAPTURE")
if __name__=="__main__":unittest.main()
