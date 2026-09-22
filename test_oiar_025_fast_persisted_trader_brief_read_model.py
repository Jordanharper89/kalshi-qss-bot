
import unittest,inspect
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_025_fast_persisted_trader_brief_read_model as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OIAR_025_BUILD_ID,"OIAR-025")
    def test_no_canonical_table(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))
if __name__=="__main__":
    print("="*88);print(" OIAR-025 CERTIFICATION TEST");print(" FAST PERSISTED TRADER BRIEF READ MODEL");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] snapshot-only trader read certified");print("[DONE] OIAR-025 CERTIFIED")
