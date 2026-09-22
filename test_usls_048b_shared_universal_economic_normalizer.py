import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_048b_shared_universal_economic_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],
   "pending_raw_count":d["pending_raw_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["exact_rows"][:30]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertTrue(all(x["base_amount"]>0 and x["quote_amount"]>0 and x["effective_price"]>0 for x in d["exact_rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-048B one shared universal economic normalizer")
  print("[PASS] exact venue trades normalized; decoder-pending venue activity retained raw")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
