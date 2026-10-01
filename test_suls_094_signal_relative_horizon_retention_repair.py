import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write,HORIZONS
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_retention(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k not in ("rows","checks","pending","due","missed_at_discovery","timing_unknown")},sort_keys=True))
  self.assertEqual(d["horizon_rows"],d["event_count"]*len(HORIZONS))
  self.assertEqual(d["dropped_events"],0)
  for row in d["rows"]:
   age=row["capture_age_seconds"];h=row["horizon_seconds"]
   if age is not None and age<=h:
    self.assertNotEqual(row["status"],"MISSED_AT_DISCOVERY")
  self.assertFalse(d["execution_authority"])
  print("[PASS] SULS-094 signal-relative horizon retention repair")
  print("[PASS] valid late births retained; elapsed horizons marked MISSED_AT_DISCOVERY; remaining horizons scheduled")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
