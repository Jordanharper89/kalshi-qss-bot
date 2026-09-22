import unittest
from qseries_v2.oracle_adapters.kalshi.oad_028_live_shadow_binding import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_028_live_shadow_postgres_persistence_binding())
    def test_both_required(self): self.assertFalse(persistence_ready(True,False))
if __name__=="__main__":
    print("="*72);print(" OAD-028 CERTIFICATION TEST");print(" LIVE SHADOW / POSTGRES PERSISTENCE BINDING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi adapter-to-Live-Shadow/PostgreSQL binding contract certified");print("[DONE] OAD-028 CERTIFIED")
