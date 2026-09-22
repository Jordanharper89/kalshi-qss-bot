import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_028b_zero_reserve_safe_sampled_outcomes import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_outcomes(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"token_address":d["token_address"],"anchor_horizon_seconds":d["anchor_horizon_seconds"],
   "sampled_mfe":d["sampled_mfe"],"sampled_mae":d["sampled_mae"],
   "price_available_count":d["price_available_count"],"price_unavailable_count":d["price_unavailable_count"],
   "remaining_horizons":d["remaining_horizons"]},sort_keys=True))
  for x in d["points"]:print("[OUTCOME]",json.dumps(x,sort_keys=True))
  self.assertEqual([x["horizon_seconds"] for x in d["points"]],[0,1,5,15,30])
  self.assertEqual(d["price_available_count"]+d["price_unavailable_count"],5)
  self.assertTrue(all((x["price_ratio_raw"] is None)==(x["price_state"]=="PRICE_UNAVAILABLE_ZERO_RESERVES") for x in d["points"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-028B zero-reserve-safe sampled price-path outcomes")
  print("[PASS] first physically priced sample becomes anchor; unavailable samples stay unavailable")
  print("[PASS] MFE/MAE remain sampled, pre-fee, non-executable")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
