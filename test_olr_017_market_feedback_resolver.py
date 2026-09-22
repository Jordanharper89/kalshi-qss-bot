import unittest
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import ProductionLearnedStateSnapshot
from qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_017_market_feedback_resolver())
    def test_unseen_abstains(self):
        s=ProductionLearnedStateSnapshot("s","l",0,0,0,"",0,0,tuple(),True)
        x=resolve_market_feedback(s,"KX")
        self.assertFalse(x.eligible);self.assertFalse(x.directional_signal_available)

if __name__=="__main__":
    print("="*72);print(" OLR-017 CERTIFICATION TEST");print(" MARKET FEEDBACK RESOLVER");print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not result.wasSuccessful():raise SystemExit(1)
    print("[PASS] Market-specific learned experience resolver certified")
    print("[PASS] No directional signal fabricated from count-only learning state")
    print("[DONE] OLR-017 CERTIFIED")
