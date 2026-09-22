import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_141_phase7_live_missing_venue_latency_cohort import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "missing_venue_row_count":d["missing_venue_row_count"],
   "family_counts":d["family_counts"],"elapsed_seconds":d["elapsed_seconds"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY")
  self.assertGreater(d["missing_venue_row_count"],0,"NO_MISSING_VENUE_ACTIVITY_IN_LIVE_COHORT")
  self.assertTrue(d["prospective"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-141 live missing-venue latency cohort")
  print("[PASS] prospective missing-venue activity captured with Oracle observation timing")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
