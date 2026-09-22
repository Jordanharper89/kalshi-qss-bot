import unittest
from qseries_v2.oracle_adapters.kalshi.oad_033_persistence_verification import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification())
if __name__=="__main__":
    print("="*72);print(" OAD-033 CERTIFICATION TEST");print(" LIVE SHADOW / POSTGRES ADVANCEMENT VERIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Existing certified OLA persistence diagnostic reuse boundary certified");print("[DONE] OAD-033 CERTIFIED")
