import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g_phase8_live_exact_trade_economics_dispatcher import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "decoded_attempt_count":d["decoded_attempt_count"],"family_support":d["family_support"],
   "ready_family_count":d["ready_family_count"],"ready_families":d["ready_families"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_ACTIVITY")
  self.assertGreater(d["decoded_attempt_count"],0,"NO_SEMANTICALLY_CERTIFIED_DECODER_ATTEMPTS")
  self.assertGreater(d["ready_family_count"],0,"NO_LIVE_MARKET_PLUS_PRICE_ROWS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161G live exact-trade economics dispatcher")
  print("[PASS] live signature -> exact family decoder -> market + price produced")
  print("[NEXT] PROSPECTIVE_SETUP_FREEZE")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
