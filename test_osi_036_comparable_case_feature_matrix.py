import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_036_comparable_case_feature_matrix import build
class T(unittest.TestCase):
 def test_future_exclusion(self):
  cur={"observed_at":"2026-09-18T18:00:00+00:00"}
  hist=[{"case_id":"past","observed_at":"2026-09-18T17:00:00+00:00","liquidity":1,"outcomes":{"60":.1}},
        {"case_id":"future","observed_at":"2026-09-18T19:00:00+00:00","liquidity":2,"outcomes":{"60":.2}}]
  d=build(cur,hist);self.assertEqual(d["case_count"],1);self.assertEqual(d["comparable_cases"][0]["case_id"],"past")
  self.assertTrue(d["future_data_excluded"]);self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-036 comparable-case feature matrix")
  print("[TRADER] Historical comparisons are frozen strictly before the live opportunity timestamp")
  print("[PASS] future_data_excluded=TRUE")
if __name__=="__main__":unittest.main()
