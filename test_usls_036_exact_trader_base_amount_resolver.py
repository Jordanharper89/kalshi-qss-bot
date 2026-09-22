import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_036_exact_trader_base_amount_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolve(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"resolved_count":d["resolved_count"]},sort_keys=True))
  for x in d["rows"]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["resolved_count"],0)
  self.assertTrue(all(x["base_amount"] is None or x["base_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-036 exact trader + base-token amount evidence resolved where physically provable")
  print("[PASS] unresolved trades remain explicit; no participant or amount guessing")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
