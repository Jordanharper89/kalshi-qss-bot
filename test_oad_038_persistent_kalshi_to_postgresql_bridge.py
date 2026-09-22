import inspect,unittest
from qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_038_persistent_kalshi_to_postgresql_bridge())
    def test_unbounded(self): self.assertIsNone(inspect.signature(run_kalshi_persistence_bridge).parameters["max_persisted"].default)
if __name__=="__main__":
    print("="*72);print(" OAD-038 CERTIFICATION TEST");print(" PERSISTENT KALSHI → OLA → POSTGRESQL BRIDGE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Persistent bridge is unbounded by default");print("[DONE] OAD-038 CERTIFIED")
