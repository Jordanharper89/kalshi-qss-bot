import unittest
from qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import MarketFeedbackResolution
from qseries_v2.oracle_learning_runtime.olr_018_scientific_reasoning_feedback_envelope import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_018_scientific_reasoning_feedback_envelope())
    def test_no_fabricated_direction(self):
        r=MarketFeedbackResolution("KX",100,100,1.0,True,False,False)
        self.assertEqual(build_scientific_reasoning_feedback_envelope(r).directional_adjustment,0.0)

if __name__=="__main__":
    print("="*72);print(" OLR-018 CERTIFICATION TEST");print(" SCIENTIFIC REASONING FEEDBACK ENVELOPE");print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not result.wasSuccessful():raise SystemExit(1)
    print("[PASS] Advisory learned-experience envelope certified")
    print("[PASS] Frozen reasoning remains authoritative")
    print("[DONE] OLR-018 CERTIFIED")
