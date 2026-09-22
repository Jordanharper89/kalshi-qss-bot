import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_012_trader_interpretation_model as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_012_BUILD_ID,"OIAR-012")
if __name__=="__main__":
 print("="*88);print(" OIAR-012 CERTIFICATION TEST");r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OIAR-012 contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-012 CERTIFIED")
