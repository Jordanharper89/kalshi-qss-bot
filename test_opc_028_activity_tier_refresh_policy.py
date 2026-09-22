import unittest
from datetime import datetime,timezone
from qseries_v2.oracle_pre_settlement_coverage import opc_028_activity_tier_refresh_policy as m
class T(unittest.TestCase):
 def test_policy(self):
  self.assertTrue(m.verify_opc_028_activity_tier_refresh_policy())
  now=datetime(2026,8,27,12,tzinfo=timezone.utc)
  self.assertEqual(m.classify_market_refresh_tier({"close_time":"2026-08-27T12:45:00Z"},now).refresh_seconds,60)
if __name__=="__main__":unittest.main(verbosity=2)
