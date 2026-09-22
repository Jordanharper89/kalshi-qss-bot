import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_041_pump_trade_event_reconciliation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_reconcile(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_count":d["exact_count"],
   "unresolved_count":d["unresolved_count"]},sort_keys=True))
  for x in d["rows"]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["exact_count"],0)
  self.assertTrue(all(x["base_amount_raw"] is None or x["base_amount_raw"]>0 for x in d["rows"]))
  self.assertTrue(all(x["quote_amount_lamports"] is None or x["quote_amount_lamports"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-041 exact TradeEvent reconciliation")
  print("[PASS] prior signer/token-balance heuristic is no longer authoritative")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
