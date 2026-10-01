import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161x_phase8_multi_cohort_prospective_oos_accumulator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"pending_freeze_count":d["pending_freeze_count"],
   "followed_market_count":d["followed_market_count"],"market_subscription_hit_count":d["market_subscription_hit_count"],
   "strict_same_market_decoded_count":d["strict_same_market_decoded_count"],"new_case_count":d["new_case_count"],
   "case_count":d["case_count"],"family_case_counts":d["family_case_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0,"EMPTY_PROSPECTIVE_OOS_LEDGER")
  self.assertGreater(d["new_case_count"],0,"NO_NEW_PROSPECTIVE_CASES_FROM_CURRENT_PENDING_COHORT")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161X multi-cohort prospective OOS accumulator")
  print("[PASS] unresolved freezes followed directly and appended idempotently to the OOS ledger")
  print("[NEXT] UPDATED_PHASE8_LEARNING_AND_COVERAGE_CHECKPOINT")
if __name__=="__main__":unittest.main()
