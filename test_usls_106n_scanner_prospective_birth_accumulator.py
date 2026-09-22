import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106n_scanner_prospective_birth_accumulator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_accumulator(self):
  p,d=write(ROOT,cycles=5,seconds_per_cycle=12,max_rows=2000)
  print("[STATE]",json.dumps({"state":d["state"],"cycles_completed":d["cycles_completed"],
   "elapsed_seconds":round(d["elapsed_seconds"],3),"birth_record_count":d["birth_record_count"],
   "trade_record_count":d["trade_record_count"],"joined_trade_count":d["joined_trade_count"],
   "unresolved_trade_count":d["unresolved_trade_count"],"accounting_ok":d["accounting_ok"]},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertTrue(d["accounting_ok"],"LIFECYCLE_ACCOUNTING_LOSS")
  self.assertGreater(d["trade_record_count"],0,"NO_PERSISTED_TRADE_ACTIVITY")
  self.assertTrue(all(x["birth_lane_error"] is None for x in d["history"]),"BIRTH_LANE_ERROR")
  self.assertTrue(all(x["trade_lane_error"] is None for x in d["history"]),"TRADE_LANE_ERROR")
  self.assertFalse(d["lifecycle_join_certified"]);self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106N prospective scanner birth accumulator")
  if d["birth_seen"]:
   print("[READY] prospective birth captured on same persistent scanner tape")
  else:
   print("[WAIT] no prospective birth yet; rerun this same test later")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
