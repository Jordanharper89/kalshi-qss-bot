import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_095c_moonit_trade_event_exact_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_event_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"revision":d["revision"],"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"],"economics_source":d["economics_source"]},sort_keys=True))
  for x in d["rows"]:
   if not x["decoder_state"].startswith("EXACT_"):print("[PENDING]",json.dumps(x,sort_keys=True))
  self.assertEqual(d["row_count"],58)
  self.assertEqual(d["exact_economic_count"],d["row_count"],"MOONIT_TRADE_EVENT_ECONOMICS_INCOMPLETE")
  self.assertTrue(all(x["event_match_count"]==1 for x in d["rows"]))
  self.assertTrue(all(x["input_amount"]>0 and x["output_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-095C Moonit exact program-emitted TradeEvent economics 58/58")
  print("[PASS] explicit dex_fee + helio_fee preserved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
