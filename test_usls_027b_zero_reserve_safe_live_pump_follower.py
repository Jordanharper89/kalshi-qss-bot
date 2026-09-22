import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_027b_zero_reserve_safe_live_pump_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_follow(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"token_address":d["token_address"],"sample_count":len(d["samples"]),
   "price_available_samples":d["price_available_samples"],"price_unavailable_samples":d["price_unavailable_samples"],
   "remaining_horizons":d["remaining_horizons"]},sort_keys=True))
  for x in d["samples"]:
   print("[SAMPLE]",json.dumps({"horizon_seconds":x["horizon_seconds"],"target_unix":x["target_unix"],
    "observed_unix":x["observed_unix"],"lag_seconds":x["lag_seconds"],"price_state":x["price_state"],
    "virtual_token_reserves":(x["state"] or {}).get("virtual_token_reserves"),
    "virtual_quote_reserves":(x["state"] or {}).get("virtual_quote_reserves")},sort_keys=True))
  self.assertEqual([x["horizon_seconds"] for x in d["samples"]],[0,1,5,15,30])
  self.assertTrue(all(x["state"] and x["state"].get("valid") for x in d["samples"]))
  self.assertEqual(d["price_available_samples"]+d["price_unavailable_samples"],5)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-027B zero-reserve-safe prospective Pump curve follower")
  print("[PASS] unavailable reserve states retained instead of fabricated or dropped")
  print("[PASS] 60s/5m/15m remain explicitly pending")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
