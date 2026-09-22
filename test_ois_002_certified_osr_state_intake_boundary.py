import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_002_certified_osr_state_intake_boundary())

    def test_read_only(self):
        self.assertTrue(build_osr_state_intake("x","uncertain",.5,.5,.2,True,"a"*64).read_only)

    def test_bounds(self):
        with self.assertRaises(ValueError):
            build_osr_state_intake("x","supported",2,.5,.1,False,"a"*64)

if __name__=="__main__":
    print("="*72);print(" OIS-002 CERTIFICATION TEST");print(" CERTIFIED OSR STATE INTAKE BOUNDARY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Frozen OSR scientific-intelligence intake boundary certified read-only")
    print("[DONE] OIS-002 CERTIFIED")
