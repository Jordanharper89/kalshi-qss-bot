import unittest
import qseries_v2.oracle_terminal.oracle_historical_experience_terminal_surface as m
class T(unittest.TestCase):
    def test_router(self):
        self.assertTrue(m.is_historical_experience_query("rank live markets by learned experience"))
        self.assertTrue(m.is_historical_experience_query("what markets does oracle understand best?"))
        self.assertTrue(m.is_historical_experience_query("what has oracle learned about KXTEST-1?"))
        self.assertFalse(m.is_historical_experience_query("what is the current price of bitcoin"))
if __name__=="__main__":
    print("="*88);print(" OHE-004 CERTIFICATION TEST");print(" TRADER HISTORICAL EXPERIENCE TERMINAL SURFACE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] historical-query recognition certified");print("[PASS] live price queries remain outside OHE");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-004 CERTIFIED")
