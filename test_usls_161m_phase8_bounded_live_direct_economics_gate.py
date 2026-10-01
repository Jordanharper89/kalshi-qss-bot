import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161m_phase8_bounded_live_direct_economics_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"router_row_count":d["router_row_count"],"target_signature_count":d["target_signature_count"],
   "hydrated_transaction_count":d["hydrated_transaction_count"],"strict_live_economic_row_count":d["strict_live_economic_row_count"],
   "family_support":d["family_support"],"rpc_source":d["rpc_source"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["target_signature_count"],0,"NO_SUPPORTED_FAMILY_LIVE_SIGNATURES_IN_WINDOW")
  self.assertGreater(d["strict_live_economic_row_count"],0,"NO_STRICT_LIVE_DIRECT_ECONOMIC_ROWS")
  self.assertTrue(all(x["strict_live_provenance"] for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161M bounded live direct economics gate")
  print("[PASS] fresh signature -> fresh transaction -> exact repo-semantic decoder -> market/economics")
  print("[NEXT] PROSPECTIVE_FEATURE_FREEZE_FROM_STRICT_LIVE_ECONOMICS")
if __name__=="__main__":unittest.main()
