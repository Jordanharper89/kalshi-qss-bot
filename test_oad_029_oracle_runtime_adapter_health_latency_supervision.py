import unittest
from qseries_v2.oracle_adapters.kalshi.oad_029_runtime_health import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_029_oracle_runtime_adapter_health_latency_supervision())
    def test_stale(self): self.assertEqual(evaluate_runtime_health(True,True,1200,20,True).status,"STALE")
    def test_persistence(self): self.assertEqual(evaluate_runtime_health(True,True,10,10,False).status,"PERSISTENCE_BLOCKED")
if __name__=="__main__":
    print("="*72);print(" OAD-029 CERTIFICATION TEST");print(" ORACLE RUNTIME ADAPTER HEALTH + LATENCY SUPERVISION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi runtime adapter health/latency supervision certified");print("[DONE] OAD-029 CERTIFIED")
