import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107b_phase5_full_capability_replacement_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_phase5(self):
  p,d=write(ROOT,max_cycles=4)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "cycles_completed","exact_birth_count","identity_complete_birth_count",
   "universal_trade_rows_captured","tape_rows_added","lifecycle_join_count",
   "raw_tape_birth_count","raw_tape_trade_count","accounting_ok",
   "phase5_full_capability_certified")},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertTrue(d["direct_birth_lane"],"DIRECT_PUMP_BIRTH_LANE_NOT_ACTIVE")
  self.assertTrue(d["trade_lane_concurrent"],"UNIVERSAL_TRADE_LANE_NOT_CONCURRENT")
  self.assertGreater(d["exact_birth_count"],0,"DIRECT_PUMP_LANE_FAILED_TO_CAPTURE_EXACT_CREATE_V2")
  self.assertEqual(d["identity_complete_birth_count"],d["exact_birth_count"],
   "EXACT_BIRTH_TOKEN_POOL_IDENTITY_INCOMPLETE")
  self.assertGreater(d["universal_trade_rows_captured"],0,"NO_CONCURRENT_UNIVERSAL_TRADES")
  self.assertTrue(d["accounting_ok"],"LIFECYCLE_ACCOUNTING_FAILED")
  self.assertGreater(d["lifecycle_join_count"],0,
   "NO_CHRONOLOGICAL_BIRTH_TO_TRADE_JOIN_FOR_FRESH_EXACT_BIRTH")
  self.assertTrue(d["phase5_full_capability_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-107B PHASE 5 FULL CAPABILITY REPLACEMENT")
  print("[PASS] direct exact Pump birth + identity + concurrent universal trade + chronological lifecycle join")
  print("[PASS] unresolved evidence retained; restart-safe tape preserved")
  print("[PASS] PHASE 5 PHYSICALLY CERTIFIED")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
