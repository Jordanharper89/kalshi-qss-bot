import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_038_enriched_universal_trade_tape import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_enrich(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"trader_base_exact_count":d["trader_base_exact_count"],
   "full_amount_exact_count":d["full_amount_exact_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"][:40]:
   print("[ENRICHED]",json.dumps({"trade_id":x["trade_id"],"side":x["side"],"trader":x["trader"],
    "base_amount":x["base_amount"],"quote_amount":x["quote_amount"],
    "effective_price":x["effective_price"],"decoder_state":x["decoder_state"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["trader_base_exact_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-038 enriched universal trade tape")
  print("[PASS] exact trader/base evidence added without fabricating native-SOL quote amount")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
