import unittest,inspect
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_038_event_time_snapshot_materializer as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_038_BUILD_ID,"OIAR-038")
 def test_stage(self):self.assertEqual(m.STAGE,"trader_event_time_snapshot")
 def test_no_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))
if __name__=="__main__":
 print("="*88);print(" OIAR-038 CERTIFICATION TEST");print(" EVENT-TIME SNAPSHOT MATERIALIZER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] precomputed event-time snapshot contract certified")
