import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162m_phase8_all14_multi_cohort_oos_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"pending_freeze_count":d["pending_freeze_count"],"followed_market_count":d["followed_market_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],"strict_same_market_decoded_count":d["strict_same_market_decoded_count"],
   "new_case_count":d["new_case_count"],"case_count":d["case_count"],"family_case_counts":d["family_case_counts"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0)
  self.assertGreater(d["new_case_count"],0,"NO_NEW_ALL14_PROSPECTIVE_CASES")
  self.assertTrue(d["all14_decoder_boundary"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162M all-14 multi-cohort OOS follower")
  print("[NEXT] UPDATED_EMPIRICAL_LEARNING_PLUS_NET_FRICTION_INTERSECTION")
if __name__=="__main__":unittest.main()
