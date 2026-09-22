
import unittest,inspect
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OIAR_026_BUILD_ID,"OIAR-026")
    def test_no_canonical_scan(self):
        s=inspect.getsource(m)
        self.assertNotIn("oracle_canonical_observations",s)
        self.assertNotIn("resolve_canonical_market_identity",s)
if __name__=="__main__":
    print("="*88);print(" OIAR-026 CERTIFICATION TEST");print(" OPERATOR TERMINAL TRADER BRIEF CUTOVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] terminal snapshot-only cutover certified");print("[DONE] OIAR-026 CERTIFIED")
