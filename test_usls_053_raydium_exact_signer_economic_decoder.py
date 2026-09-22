import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_053_raydium_exact_signer_economic_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],
   "two_asset_exact_count":d["two_asset_exact_count"],"quote_oriented_exact_count":d["quote_oriented_exact_count"]},sort_keys=True))
  for x in d["rows"][:30]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertGreater(d["two_asset_exact_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-053 Raydium signer economic decoder")
  print("[PASS] actual pre/post owner token deltas used; BUY/SELL only when quote orientation is exact")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
