import unittest
from qseries_v2.oracle_continuous_learner.ocl_019_narrative_market_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_019_narrative_market_relationship_learning())
    def test_mean_lag(self): self.assertEqual(learn_narrative_market_relationship("n","m",((1,2),(1,4))).mean_lag_seconds,3)
    def test_required(self):
        with self.assertRaises(ValueError): learn_narrative_market_relationship("","m",((1,1),))

if __name__=="__main__":
    print("="*72);print(" OCL-019 CERTIFICATION TEST");print(" NARRATIVE-TO-MARKET RELATIONSHIP LEARNING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Historical narrative-to-market reaction learning certified")
    print("[DONE] OCL-019 CERTIFIED")
