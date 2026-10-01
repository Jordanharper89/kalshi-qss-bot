import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_051_historical_feature_outcome_join_contract import join
class T(unittest.TestCase):
 def test_join(self):
  f=[{"observation_id":"a","observed_at":"2026-09-01T00:00:00+00:00","features":{"liquidity":1}}]
  o=[{"observation_id":"a","outcomes":{"60":.1}}]
  d=join(f,o);self.assertEqual(d["case_count"],1);self.assertEqual(d["cases"][0]["outcomes"]["60"],.1)
  print("[PASS] OSI-051 historical feature/outcome join contract")
  print("[TRADER] Locks the exact case shape scientific formula discovery will consume")
if __name__=="__main__":unittest.main()
