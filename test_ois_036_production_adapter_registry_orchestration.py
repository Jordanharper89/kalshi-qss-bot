import unittest
from qseries_v2.oracle_intelligence_state.ois_036_adapter_registry import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_036_production_adapter_registry_orchestration())

    def test_duplicate(self):
        a=register_adapter("a","v")
        with self.assertRaises(ValueError):
            build_adapter_registry((a,a))

    def test_full_universe_default(self):
        self.assertTrue(register_adapter("a","v").supports_full_universe)

if __name__=="__main__":
    print("="*72);print(" OIS-036 CERTIFICATION TEST");print(" PRODUCTION ADAPTER REGISTRY + ORCHESTRATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Production adapter registry/orchestration foundation certified")
    print("[DONE] OIS-036 CERTIFIED")
