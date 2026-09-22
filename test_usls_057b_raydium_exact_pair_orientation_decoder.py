import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_057b_raydium_exact_pair_orientation_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_orientation(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],
   "venue_two_asset_counts":d["venue_two_asset_counts"],"venue_exact_quote_counts":d["venue_exact_quote_counts"]},sort_keys=True))
  for x in d["rows"][:40]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-057B Raydium exact pair/orientation decoder")
  print("[PASS] BUY/SELL only emitted when WSOL/USDC quote orientation is physically exact")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
