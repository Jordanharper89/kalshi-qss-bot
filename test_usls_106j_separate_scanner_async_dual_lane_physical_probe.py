import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106j_separate_scanner_async_dual_lane_physical_probe import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT,seconds=12,max_rows=2000)
  print("[STATE]",json.dumps({
   "runtime":d["runtime"],
   "elapsed_seconds":round(d["elapsed_seconds"],3),
   "birth_lane":d["birth_lane"],
   "birth_before_count":d["birth_before_count"],
   "birth_after_count":d["birth_after_count"],
   "new_birth_count":d["new_birth_count"],
   "trade_return_type":d["trade_return_type"],
   "trade_row_count":d["trade_row_count"],
   "trade_lane_error":d["trade_lane_error"],
   "async_execution_verified":d["async_execution_verified"]},sort_keys=True))
  self.assertTrue(d["async_execution_verified"])
  self.assertTrue(d["birth_lane"]["started"])
  self.assertIsNone(d["birth_lane"]["error"],"BIRTH_LANE_ASYNC_CAPTURE_FAILED")
  self.assertIsNone(d["trade_lane_error"],"TRADE_LANE_ASYNC_CAPTURE_FAILED")
  self.assertNotEqual(d["trade_return_type"],"coroutine","TRADE_COROUTINE_NOT_AWAITED")
  self.assertGreater(d["trade_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY_CAPTURED")
  self.assertGreater(d["elapsed_seconds"],1.0,"BOUNDED_PROBE_RETURNED_TOO_FAST_TO_BE_PHYSICAL")
  self.assertFalse(d["production_activation_claimed"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106J async dual-lane Solana Scanner physical probe")
  print("[PASS] birth and universal trade coroutines physically awaited")
  print("[PASS] lifecycle join remains uncertified")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
