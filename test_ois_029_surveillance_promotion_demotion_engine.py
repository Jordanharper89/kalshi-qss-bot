import unittest
from qseries_v2.oracle_intelligence_state.ois_028_tier_classification import SurveillanceTierDecision
from qseries_v2.oracle_intelligence_state.ois_029_tier_transition import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_029_surveillance_promotion_demotion_engine())

    def test_demote(self):
        d=SurveillanceTierDecision("kalshi","A","COLD","low_activity",True,30)
        self.assertEqual(transition_surveillance_tier("ACTIVE",d).direction,"DEMOTE")

    def test_hold(self):
        d=SurveillanceTierDecision("kalshi","A","ACTIVE","active_market",True,1)
        self.assertEqual(transition_surveillance_tier("ACTIVE",d).direction,"HOLD")

if __name__=="__main__":
    print("="*72);print(" OIS-029 CERTIFICATION TEST");print(" SURVEILLANCE PROMOTION + DEMOTION ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Dynamic surveillance promotion/demotion semantics certified")
    print("[DONE] OIS-029 CERTIFIED")
