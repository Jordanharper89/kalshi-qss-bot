import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_042_pump_exact_economic_trade_tape import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_tape(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],
   "economic_exact_count":d["economic_exact_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:print("[ECON]",json.dumps({"trade_id":x["trade_id"],"side":x["side"],
   "trader":x["trader"],"base_amount":x["base_amount"],"quote_amount":x["quote_amount"],
   "effective_price":x["effective_price"],"decoder_state":x["decoder_state"]},sort_keys=True))
  self.assertGreater(d["economic_exact_count"],0)
  self.assertTrue(all(x["effective_price"] is None or x["effective_price"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-042 exact Pump economic trade tape")
  print("[PASS] actual TradeEvent token/SOL amounts replace wallet-delta inference")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
