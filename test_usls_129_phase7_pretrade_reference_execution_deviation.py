import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_129_phase7_pretrade_reference_execution_deviation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],
   "bounded_reference_count":d["bounded_reference_count"],
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["bounded_reference_count"],0,"NO_BOUNDED_PRE_TRADE_REFERENCE_ROWS")
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertIn("NOT_PURE_AMM_SLIPPAGE",d["deviation_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-129 pre-trade reference / execution deviation")
  print("[PASS] bounded prior observed trade used without calling market movement pure slippage")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
