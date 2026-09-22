import unittest
from qseries_v2.oracle_intelligence_state.ois_028_tier_classification import SurveillanceTierDecision
from qseries_v2.oracle_intelligence_state.ois_034_freshness_enforcement import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_034_freshness_staleness_enforcement())

    def test_active_one_second(self):
        d=SurveillanceTierDecision("k","m","ACTIVE","x",True,1.0)
        self.assertTrue(evaluate_market_freshness(d,1.01).stale)

    def test_dead_blocks(self):
        d=SurveillanceTierDecision("k","m","DEAD","x",False,None)
        self.assertTrue(evaluate_market_freshness(d,100).block_handoff)

if __name__=="__main__":
    print("="*72);print(" OIS-034 CERTIFICATION TEST");print(" FRESHNESS + STALENESS ENFORCEMENT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Tier-aware market freshness/staleness enforcement certified")
    print("[DONE] OIS-034 CERTIFIED")
