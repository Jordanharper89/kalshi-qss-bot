import unittest
from qseries_v2.oracle_adapters.oad_004_lifecycle_health import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_004_adapter_lifecycle_health_contract())

    def test_down_requires_recovery(self):
        x = build_adapter_lifecycle_state("a","DOWN",False,False,False,0)
        self.assertTrue(evaluate_adapter_health(x).recovery_required)

    def test_lagging(self):
        x = build_adapter_lifecycle_state("a","LIVE",True,True,True,6)
        self.assertEqual(evaluate_adapter_health(x).status,"LAGGING")

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-004 CERTIFICATION TEST")
    print(" ADAPTER LIFECYCLE + HEALTH CONTRACT")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Adapter lifecycle/health contract certified")
    print("[DONE] OAD-004 CERTIFIED")
