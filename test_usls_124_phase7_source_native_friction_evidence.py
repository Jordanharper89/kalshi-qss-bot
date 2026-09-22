import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_124_phase7_source_native_friction_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fee=sum(v["fee"] for v in d["family_support"].values())
  liq=sum(v["liquidity"] for v in d["family_support"].values())
  pre=sum(v["pre_reference"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"fee_rows":fee,
   "liquidity_rows":liq,"pre_reference_rows":pre,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(fee+liq,0,"NO_SOURCE_NATIVE_FRICTION_EVIDENCE_FOUND")
  self.assertEqual(d["slippage_policy"],"NO_SLIPPAGE_CLAIM_WITHOUT_PRE_TRADE_REFERENCE_STATE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-124 source-native friction evidence")
  print("[PASS] fee/liquidity/reserve evidence preserved without invented slippage")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
