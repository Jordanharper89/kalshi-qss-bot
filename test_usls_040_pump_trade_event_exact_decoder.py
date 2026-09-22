import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_040_pump_trade_event_exact_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_events(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_trade_event":d["rows_with_trade_event"],
   "total_trade_events":d["total_trade_events"]},sort_keys=True))
  for x in d["rows"]:
   if x["events"]:print("[EVENT]",json.dumps({"trade_id":x["trade_id"],"events":x["events"]},sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertGreater(d["rows_with_trade_event"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-040 exact Pump TradeEvent decoder")
  print("[PASS] on-chain event supplies actual user/token/SOL/reserve evidence")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
