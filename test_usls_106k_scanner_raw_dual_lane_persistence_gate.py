import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106k_scanner_raw_dual_lane_persistence_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,seconds=12,max_rows=2000)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIsNone(d["trade_lane_error"],"TRADE_LANE_FAILED")
  self.assertGreater(d["session_trade_rows"],0,"NO_LIVE_TRADE_ROWS")
  self.assertGreater(d["persisted_trade_rows"]+d["deduplicated_existing_rows"],0,"NO_TRADE_ROWS_RETAINED")
  self.assertTrue(d["raw_retention"]);self.assertTrue(d["restart_safe_append"])
  self.assertFalse(d["lifecycle_join_certified"]);self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106K scanner raw dual-lane persistence gate")
  print("[PASS] live trade activity retained in restart-safe scanner tape")
  print("[PASS] zero-birth windows remain valid; lifecycle join remains uncertified")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
