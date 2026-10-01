import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q
class T(unittest.TestCase):
 def test_active(self):self.assertEqual(q.classify({"status":"ACTIVE","samples":3,"wins":3,"pnl_sol":1,"last_profitable_unix":100},101),"ACTIVE")
 def test_age_rechecks_not_retires(self):self.assertEqual(q.classify({"status":"ACTIVE","samples":8,"wins":7,"pnl_sol":1,"last_profitable_unix":100},1000),"RECHECK")
 def test_retirement_requires_bad_economics(self):self.assertEqual(q.classify({"status":"ACTIVE","samples":6,"wins":1,"pnl_sol":-.01,"last_profitable_unix":100},101),"RETIRED")
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
