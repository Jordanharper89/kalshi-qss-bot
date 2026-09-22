import unittest
from qseries_v2.oracle_intelligence_state.ois_027_full_universe_state import build_market_surveillance_state
from qseries_v2.oracle_intelligence_state.ois_028_tier_classification import *

class T(unittest.TestCase):
    def state(self,tradable=True,liq=.5,act=.5):
        return build_market_surveillance_state("kalshi","A","x",tradable,1,1,liq,act)

    def test_verifier(self):
        self.assertTrue(verify_ois_028_surveillance_tier_classification())

    def test_ultra_hot(self):
        self.assertEqual(classify_surveillance_tier(self.state(),near_qseries_threshold=True).tier,"ULTRA_HOT")

    def test_dead(self):
        self.assertEqual(classify_surveillance_tier(self.state(False,0,0)).tier,"DEAD")

    def test_active_one_second(self):
        self.assertEqual(classify_surveillance_tier(self.state(True,.7,.6)).max_scheduled_refresh_seconds,1.0)

if __name__=="__main__":
    print("="*72);print(" OIS-028 CERTIFICATION TEST");print(" SURVEILLANCE-TIER CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] ULTRA-HOT/HOT/ACTIVE/WARM/COLD/DORMANT/DEAD classification certified")
    print("[DONE] OIS-028 CERTIFIED")
