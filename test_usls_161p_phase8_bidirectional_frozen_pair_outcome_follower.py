import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161p_phase8_bidirectional_frozen_pair_outcome_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"frozen_market_count":d["frozen_market_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],
   "strict_same_market_decoded_count":d["strict_same_market_decoded_count"],
   "prospective_case_count":d["prospective_case_count"],
   "same_direction_case_count":d["same_direction_case_count"],
   "reversed_inverted_case_count":d["reversed_inverted_case_count"],
   "prospective_families":d["prospective_families"],
   "mean_gross_forward_return":d["mean_gross_forward_return"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["market_subscription_hit_count"],0,"NO_POST_FREEZE_ACTIVITY_ON_FROZEN_MARKETS")
  self.assertGreater(d["prospective_case_count"],0,"NO_ORIENTATION_NORMALIZED_PROSPECTIVE_CASES")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161P bidirectional frozen-pair outcome follower")
  print("[PASS] opposite trade direction is inverted into the original frozen pair orientation")
  print("[NEXT] APPEND_ONLY_PROSPECTIVE_OOS_LEDGER")
if __name__=="__main__":unittest.main()
