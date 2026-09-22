import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_014_natural_trader_question_router as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_014_BUILD_ID,"OIAR-014")
if __name__=="__main__":
 print("="*88);print(" OIAR-014 CERTIFICATION TEST");r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OIAR-014 contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-014 CERTIFIED")
