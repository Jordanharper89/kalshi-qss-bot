import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o2_phase8_exact_frozen_market_outcome_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"frozen_market_count":d["frozen_market_count"],
   "frozen_setup_count":d["frozen_setup_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],
   "hydrated_transaction_count":d["hydrated_transaction_count"],
   "strict_same_market_decoded_count":d["strict_same_market_decoded_count"],
   "prospective_case_count":d["prospective_case_count"],
   "prospective_families":d["prospective_families"],
   "mean_gross_forward_return":d["mean_gross_forward_return"],
   "net_case_count":d["net_case_count"],
   "mean_net_forward_return":d["mean_net_forward_return"],
   "profitability_decision":d["profitability_decision"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["frozen_market_count"],0,"NO_FROZEN_MARKETS")
  self.assertGreater(d["market_subscription_hit_count"],0,
   "NO_POST_FREEZE_ACTIVITY_ON_EXACT_FROZEN_MARKETS_WITHIN_WINDOW")
  self.assertGreater(d["prospective_case_count"],0,
   "FROZEN_MARKETS_ACTIVE_BUT_NO_STRICT_SAME_PAIR_PROSPECTIVE_CASES")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161O2 exact frozen-market prospective outcome follower")
  print("[PASS] outcome collection follows the frozen cohort instead of resampling random Solana markets")
  print("[STATE]",d["profitability_decision"])
  print("[NEXT]",d["next_boundary"])
if __name__=="__main__":unittest.main()
