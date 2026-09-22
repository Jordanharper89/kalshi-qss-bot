import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_053_proven_current_market_history as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_053_BUILD_ID,"OIAR-053")
 def test_physical(self):
  x=m.read_latest_current_market_history();self.assertTrue(x);self.assertGreater(x["market_count"],0);self.assertTrue(all(v["history_rows"]>0 for v in x["markets"]))
if __name__=="__main__":
 print("="*88);print(" OIAR-053 CERTIFICATION TEST");print(" PROVEN CURRENT MARKET HISTORY");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] exact indexed current-market history certified");print("[DONE] OIAR-053 CERTIFIED")
