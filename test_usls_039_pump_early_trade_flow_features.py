import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_039_pump_early_trade_flow_features import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_features(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("trade_count","buy_count","sell_count","unique_trader_count",
   "median_intertrade_seconds","trades_per_second","quote_flow_available","profitability_claimed")},sort_keys=True))
  for x in d["windows"]:print("[WINDOW]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["trade_count"],0)
  self.assertEqual(d["buy_count"]+d["sell_count"],d["trade_count"])
  self.assertEqual([x["horizon_seconds"] for x in d["windows"]],[5,15,30])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-039 Pump early trade-flow features built from physical trade tape")
  print("[PASS] 5s/15s/30s buyer-seller flow now measurable without inventing quote flow")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
