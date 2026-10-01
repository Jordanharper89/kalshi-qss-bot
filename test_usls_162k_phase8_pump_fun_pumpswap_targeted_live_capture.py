import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162k_phase8_pump_fun_pumpswap_targeted_live_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"signature_count":d["signature_count"],"hydrated_transaction_count":d["hydrated_transaction_count"],
   "strict_live_economic_row_count":d["strict_live_economic_row_count"],"family_support":d["family_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["signature_count"],0,"NO_TARGETED_PUMP_SIGNATURES")
  self.assertGreater(d["strict_live_economic_row_count"],0,"NO_TARGETED_PUMP_STRICT_LIVE_ECONOMICS")
  self.assertIn("PUMP_FUN",d["family_support"],"PUMP_FUN_LIVE_ECONOMICS_NOT_CAPTURED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162K Pump.fun + PumpSwap targeted live capture")
  print("[NEXT] FREEZE_PUMP_FUN_AND_PUMPSWAP_TARGETED_COHORTS")
if __name__=="__main__":unittest.main()
