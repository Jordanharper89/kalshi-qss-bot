import unittest
from qseries_v2.oracle_intelligence_state.ois_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_001_intelligence_state_foundation())

    def test_deterministic_identity(self):
        a=build_intelligence_state_identity("x","a"*64,"b"*64)
        b=build_intelligence_state_identity("x","a"*64,"b"*64)
        self.assertEqual(a.state_id,b.state_id)

    def test_bad_hash(self):
        with self.assertRaises(ValueError):
            build_intelligence_state_identity("x","bad","b"*64)

if __name__=="__main__":
    print("="*72);print(" OIS-001 CERTIFICATION TEST");print(" ORACLE INTELLIGENCE STATE FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic terminal-independent intelligence-state foundation certified")
    print("[DONE] OIS-001 CERTIFIED")
