import unittest
from qseries_v2.oracle_adapters.kalshi.oad_019_hot_active_routing import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_019_kalshi_hot_active_surveillance_routing())
    def test_ultra_hot(self): self.assertEqual(route_market("A",True,.1,.1,near_qseries_threshold=True).tier,"ULTRA_HOT")
    def test_active_one_second(self): self.assertEqual(route_market("A",True,.6,.7).max_scheduled_refresh_seconds,1.0)
    def test_dead_archive(self): self.assertEqual(route_market("A",False,0,0).route,"ARCHIVE")
if __name__=="__main__":
    print("="*72);print(" OAD-019 CERTIFICATION TEST");print(" KALSHI HOT / ACTIVE / BROAD SURVEILLANCE ROUTING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi dynamic HOT/ACTIVE/broad-surveillance routing certified");print("[DONE] OAD-019 CERTIFIED")
