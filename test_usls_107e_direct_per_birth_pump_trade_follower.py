import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107e_direct_per_birth_pump_trade_follower import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_phase5(self):
  p,d=write(ROOT,max_signatures=100)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "birth_count","exact_trade_count","normalized_rows_added",
   "exact_identity_lifecycle_join_count","join_finding",
   "phase5_full_capability_certified")},sort_keys=True))
  for x in d["per_birth"]: print("[BIRTH_FOLLOW]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_count"],0,"NO_EXACT_PUMP_BIRTHS_AVAILABLE")
  self.assertTrue(d["direct_per_birth_follow"])
  self.assertTrue(d["exact_tradeevent_required"])
  self.assertTrue(d["token_and_curve_required"])
  self.assertGreater(d["exact_trade_count"],0,
   "NO_EXACT_PUMP_TRADEEVENT_FOUND_FOR_FRESH_BIRTH_CURVE")
  self.assertGreater(d["exact_identity_lifecycle_join_count"],0,
   "NO_EXACT_BIRTH_TO_TRADE_LIFECYCLE_JOIN")
  self.assertTrue(d["phase5_full_capability_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-107E direct per-birth Pump trade follower")
  print("[PASS] exact Pump TradeEvent + token + curve identity normalized")
  print("[PASS] chronological exact birth-to-trade lifecycle join")
  print("[PASS] PHASE 5 PHYSICALLY CERTIFIED")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
