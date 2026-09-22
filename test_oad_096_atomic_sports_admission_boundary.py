import unittest
from qseries_v2.oracle_adapters.independent.oad_096_atomic_sports_admission_boundary import *

class T(unittest.TestCase):
    def test_non_sport(self):
        r=atomic_sports_admission({"ticker":"X","title":"Will CPI inflation exceed 3 percent?"})
        self.assertNotEqual(r.admitted_domain,"sports")
    def test_unknown_is_explicit(self):
        r=atomic_sports_admission({"ticker":"X","title":"Over 41.5 points scored"})
        self.assertFalse(r.admitted_domain=="sports" and r.league=="NONE")
    def test_verifier(self):
        self.assertTrue(verify_no_sports_none((AtomicSportsAdmission("X","sports","sports_unresolved","UNKNOWN","UNRESOLVED",()),)))

if __name__=="__main__":
    print("="*88);print(" OAD-096 CERTIFICATION TEST");print(" ATOMIC SPORTS ADMISSION BOUNDARY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] sports/NONE state eliminated by atomic admission")
    print("[DONE] OAD-096 CERTIFIED")
