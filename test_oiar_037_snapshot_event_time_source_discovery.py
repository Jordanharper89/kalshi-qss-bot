import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_037_snapshot_event_time_source_discovery as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_037_BUILD_ID,"OIAR-037")
 def test_fields(self):self.assertIn("source_close_time",m.TIME_FIELDS)
 def test_boundary(self):self.assertFalse(m.EXECUTION_AUTHORITY)
if __name__=="__main__":
 print("="*88);print(" OIAR-037 CERTIFICATION TEST");print(" SNAPSHOT EVENT-TIME SOURCE DISCOVERY");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] snapshot-native event-time discovery contract certified")
