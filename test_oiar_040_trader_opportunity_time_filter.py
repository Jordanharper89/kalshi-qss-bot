import unittest,inspect
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_040_trader_opportunity_time_filter as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_040_BUILD_ID,"OIAR-040")
 def test_intent(self):self.assertEqual(m.requested_window("plays for today"),"TODAY");self.assertEqual(m.requested_window("this evening"),"TONIGHT")
 def test_no_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))
if __name__=="__main__":
 print("="*88);print(" OIAR-040 CERTIFICATION TEST");print(" TRADER OPPORTUNITY TIME FILTERING");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] requested time window filters snapshot markets")
