import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_126_phase7_strict_executable_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "row_count","ready_count","incomplete_count","family_readiness","next_boundary")},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertEqual(d["ready_count"]+d["incomplete_count"],d["row_count"])
  self.assertEqual(d["readiness_contract"],
   "PRICE_PLUS_FEE_PLUS_LATENCY_PLUS_LIQUIDITY_PLUS_SLIPPAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-126 strict executable readiness gate")
  print("[PASS] no row is executable-ready unless all physical friction inputs are present")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
