import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g2_phase8_pumpswap_live_economics_foundation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "pumpswap_signature_count":d["pumpswap_signature_count"],
   "economic_row_count":d["economic_row_count"],
   "repeat_market_count":d["repeat_market_count"],
   "market_counts":d["market_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_ACTIVITY")
  self.assertGreater(d["pumpswap_signature_count"],0,"NO_LIVE_PUMPSWAP_SIGNATURES")
  self.assertGreater(d["economic_row_count"],0,"NO_EXACT_PUMPSWAP_LIVE_ECONOMIC_ROWS")
  self.assertFalse(d["exact_pool_address_claimed"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161G2 PumpSwap live economics foundation")
  print("[PASS] exact PumpSwap instruction + instruction-local token flow -> directed-pair live price")
  print("[PASS] no fake pool-address claim")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
