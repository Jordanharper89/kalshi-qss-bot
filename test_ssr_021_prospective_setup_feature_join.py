import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_021_prospective_setup_feature_join import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_join(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"joined_case_count":d["joined_case_count"],"family_counts":d["family_counts"]},sort_keys=True))
  self.assertGreater(d["joined_case_count"],0)
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-021 prospective setup-feature join")
if __name__=="__main__":
 unittest.main()
