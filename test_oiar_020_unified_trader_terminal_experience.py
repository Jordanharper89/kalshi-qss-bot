import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_020_unified_trader_terminal_experience import is_unified_trader_query,OIAR_020_BUILD_ID
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OIAR_020_BUILD_ID,"OIAR-020")
    def test_route(self):self.assertTrue(is_unified_trader_query("what do you like right now"))
if __name__=="__main__":
    print("="*88);print(" OIAR-020 CERTIFICATION TEST");print(" UNIFIED TRADER TERMINAL EXPERIENCE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] unified trader terminal query contract certified")
    print("[DONE] OIAR-020 CERTIFIED")
