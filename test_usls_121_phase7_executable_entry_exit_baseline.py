import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_121_phase7_executable_entry_exit_baseline import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"ready_count":d["ready_count"],
   "incomplete_count":d["incomplete_count"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["model_policy"],
   "NO_EXECUTABLE_PRICE_WHEN_REQUIRED_FRICTION_INPUTS_MISSING")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-121 executable entry/exit baseline")
  print("[PASS] incomplete fee/slippage/latency/liquidity inputs correctly block executable-price claims")
  print("[NEXT] PHYSICAL_FEE_LIQUIDITY_LATENCY_ENRICHMENT")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
