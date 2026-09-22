import unittest
from qseries_v2.oracle_learning_runtime.olr_038_learning_staleness_contradiction_guard import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_038_learning_staleness_contradiction_guard())
    def test_contradiction_blocks(self):self.assertFalse(evaluate_learning_guard(None,contradiction_score=.8).allowed)

if __name__=="__main__":
    print("="*72);print(" OLR-038 CERTIFICATION TEST");print(" LEARNING STALENESS + CONTRADICTION GUARD");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Stale/contradictory learning suppression certified")
    print("[DONE] OLR-038 CERTIFIED")
