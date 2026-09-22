import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_064_current_thesis_cohort_support as m
class T(unittest.TestCase):
 def test_physical(self):
  x=m.read_latest_current_thesis_cohort_support();self.assertTrue(x);self.assertGreater(len(x["markets"]),0)
  self.assertTrue(all(v["empirical_rate"] is None for v in x["markets"]))
if __name__=="__main__":
 print("="*88);print(" OIAR-064 CERTIFICATION TEST\n CURRENT THESIS COHORT SUPPORT");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] thesis cohort support certified");print("[PASS] no unsupported probability emitted");print("[DONE] OIAR-064 CERTIFIED")
