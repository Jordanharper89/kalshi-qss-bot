import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_029b_restart_safe_price_availability_outcome_store import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_store(self):
  p,d=write(ROOT);n1=len(d["cases"]);p,d2=write(ROOT);n2=len(d2["cases"])
  latest=max(d2["cases"].values(),key=lambda x:x.get("updated_unix",0))
  print("[STATE]",json.dumps({"case_count_first":n1,"case_count_second":n2,
   "point_count":len(latest["points"]),"anchor_horizon_seconds":latest["anchor_horizon_seconds"],
   "price_available_count":latest["price_available_count"],"price_unavailable_count":latest["price_unavailable_count"],
   "pending_horizons":latest["pending_horizons"],"profitability_eligible":latest["profitability_eligible"]},sort_keys=True))
  self.assertEqual(n1,n2);self.assertGreater(n2,0)
  self.assertEqual([x["horizon_seconds"] for x in latest["points"]],[0,1,5,15,30])
  self.assertEqual(latest["price_available_count"]+latest["price_unavailable_count"],5)
  self.assertEqual(latest["pending_horizons"],[60,300,900])
  self.assertFalse(latest["profitability_eligible"]);self.assertFalse(d2["execution_authority"])
  print("[PASS] USLS-029B restart-safe Pump outcome store with price-availability lineage")
  print("[PASS] zero-reserve states survive restart and remain scientifically explicit")
  print("[PASS] 60s/5m/15m remain pending without fabrication")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
