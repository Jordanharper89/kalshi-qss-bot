import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_125_phase7_physical_friction_merge import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  partial=sum(v["partial"] for v in d["family_support"].values())
  slip=sum(v["slippage_ready"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"partial_rows":partial,
   "slippage_ready_rows":slip,"family_support":d["family_support"]},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertGreater(partial,0,"NO_PHYSICAL_FRICTION_EVIDENCE_MERGED")
  self.assertEqual(d["network_fee_conversion_policy"],
   "LAMPORTS_RETAINED_SEPARATELY_UNLESS_QUOTE_DENOMINATION_PROVEN")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-125 physical friction merge")
  print("[PASS] on-chain fee/latency + source-native liquidity evidence merged conservatively")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
