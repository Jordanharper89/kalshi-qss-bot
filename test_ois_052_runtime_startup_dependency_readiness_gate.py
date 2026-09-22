import unittest
from qseries_v2.oracle_intelligence_state.ois_052_startup_readiness import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_052_runtime_startup_dependency_readiness_gate())

    def test_missing_blocks(self):
        states=tuple(StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES[:-1])
        self.assertFalse(evaluate_startup_readiness(states).permitted_to_run)

    def test_uncertified_blocks(self):
        states=[StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES]
        states[-1]=StartupDependencyState("ois",True,False)
        self.assertIn("ois",evaluate_startup_readiness(states).missing_or_unready)

if __name__=="__main__":
    print("="*72);print(" OIS-052 CERTIFICATION TEST");print(" RUNTIME STARTUP DEPENDENCY + READINESS GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Oracle startup dependency/readiness gate certified")
    print("[DONE] OIS-052 CERTIFIED")
