import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162c_phase8_extended_multi_cohort_oos_accumulator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"pending_freeze_count":d["pending_freeze_count"],"followed_market_count":d["followed_market_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],"new_case_count":d["new_case_count"],"case_count":d["case_count"],
   "family_case_counts":d["family_case_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0)
  self.assertGreater(d["new_case_count"],0,"NO_NEW_CASES_FROM_EXTENDED_COHORT")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162C extended multi-cohort OOS accumulator")
  print("[NEXT] LINK_ONLY_PHYSICAL_FRICTION_AND_RECHECK_PHASE8")
if __name__=="__main__":unittest.main()
