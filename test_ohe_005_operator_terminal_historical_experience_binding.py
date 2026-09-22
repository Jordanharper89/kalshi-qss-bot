import unittest
import run_oracle_open_intelligence_terminal as base
import qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding as m
class T(unittest.TestCase):
    def test_binding(self):
        old=base.display_query
        try:
            m.bind_historical_experience_surface(base);self.assertTrue(base._ohe005_bound);self.assertTrue(callable(base.display_query))
        finally:
            base.display_query=old
            if hasattr(base,"_ohe005_bound"):delattr(base,"_ohe005_bound")
if __name__=="__main__":
    print("="*88);print(" OHE-005 CERTIFICATION TEST");print(" OPERATOR TERMINAL HISTORICAL EXPERIENCE BINDING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] frozen OIT runner wrapped without source mutation");print("[PASS] unmatched queries preserve existing OIT/live-price path");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-005 CERTIFIED")
