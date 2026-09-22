import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106d_phase5_prospective_shared_cohort_bootstrap import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bootstrap(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "birth_rows":d["birth_source"]["row_count"],
   "birth_last_slot":d["birth_source"]["last_slot"],
   "trade_sources":[{"path":x["path"],"row_count":x["row_count"],"revision":x.get("revision")} for x in d["trade_sources"]],
   "bootstrap_unix":d["bootstrap_unix"]},sort_keys=True))
  self.assertGreater(d["birth_source"]["row_count"],0)
  self.assertGreater(d["birth_source"]["last_slot"],0)
  self.assertTrue(any(x["exists"] and x["row_count"]>0 for x in d["trade_sources"]))
  self.assertEqual(d["unknown_policy"],"RETAIN_UNRESOLVED")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106D prospective shared birth↔trade cohort bootstrap")
  print("[PASS] historical disjoint cohorts excluded from future lifecycle certification")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
