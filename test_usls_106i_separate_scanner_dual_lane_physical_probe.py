import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106i_separate_scanner_dual_lane_physical_probe import write
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
   "trade_lane_error":d["trade_lane_error"]},sort_keys=True))
  self.assertTrue(d["birth_lane"]["started"])
  self.assertIsNone(d["trade_lane_error"],"TRADE_LANE_PHYSICAL_CAPTURE_FAILED")
  self.assertGreater(d["trade_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY_CAPTURED")
  self.assertFalse(d["production_activation_claimed"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106I separate Solana Scanner dual-lane physical probe")
  print("[PASS] live universal trade acquisition physically active")
  print("[PASS] birth lane invoked concurrently; join remains uncertified")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
