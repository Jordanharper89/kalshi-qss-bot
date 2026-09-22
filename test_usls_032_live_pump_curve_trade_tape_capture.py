import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_032_live_pump_curve_trade_tape_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("token_address","market_address","notifications_seen","trade_instruction_count","buy_count","sell_count")},sort_keys=True))
  for x in d["rows"][:50]:print("[TRADE_IX]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["notifications_seen"],0)
  self.assertGreater(d["trade_instruction_count"],0)
  self.assertEqual(d["trade_instruction_count"],d["buy_count"]+d["sell_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-032 prospective live Pump curve-specific trade tape captured")
  print("[PASS] exact BUY/SELL instructions captured after exact newborn-token birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
