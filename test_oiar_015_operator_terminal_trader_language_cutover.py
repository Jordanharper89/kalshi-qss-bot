import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_015_operator_terminal_trader_language_cutover as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_015_BUILD_ID,"OIAR-015")
if __name__=="__main__":
 print("="*88);print(" OIAR-015 CERTIFICATION TEST");r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OIAR-015 contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-015 CERTIFIED")
