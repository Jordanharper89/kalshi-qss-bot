import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_034_restart_safe_universal_trade_tape_store import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_store(self):
  p,d,b1,a1=write(ROOT);p,d2,b2,a2=write(ROOT)
  rows=list(d2["trades"].values())
  print("[STATE]",json.dumps({"first_before":b1,"first_after":a1,"second_before":b2,"second_after":a2,
   "trade_count":d2["trade_count"],"buy_count":sum(1 for x in rows if x["side"]=="BUY"),
   "sell_count":sum(1 for x in rows if x["side"]=="SELL")},sort_keys=True))
  self.assertGreater(a1,0);self.assertEqual(a1,a2)
  self.assertEqual(d2["trade_count"],len(d2["trades"]))
  self.assertFalse(d2["execution_authority"])
  print("[PASS] USLS-034 restart-safe idempotent universal Solana trade-tape store")
  print("[PASS] exact Pump BUY/SELL observations survive rerun without duplication")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
