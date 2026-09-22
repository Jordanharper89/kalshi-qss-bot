import unittest
from qseries_v2.oracle_intelligence_state.ois_036_adapter_registry import register_adapter
from qseries_v2.oracle_intelligence_state.ois_037_adapter_health import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_037_adapter_readiness_health())

    def test_down(self):
        a=register_adapter("a","v")
        self.assertEqual(evaluate_adapter_health(a,False,False,False,0).status,"DOWN")

    def test_lagging(self):
        a=register_adapter("a","v")
        self.assertEqual(evaluate_adapter_health(a,True,True,True,6).status,"LAGGING")

if __name__=="__main__":
    print("="*72);print(" OIS-037 CERTIFICATION TEST");print(" ADAPTER READINESS + HEALTH");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Adapter readiness/health classification certified")
    print("[DONE] OIS-037 CERTIFIED")
