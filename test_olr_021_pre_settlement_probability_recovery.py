import unittest
from qseries_v2.oracle_learning_runtime.olr_021_pre_settlement_probability_recovery import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_021_pre_settlement_probability_recovery())
    def test_decimal_probability(self):
        x=recover_pre_settlement_probability({"probability":0.71})
        self.assertAlmostEqual(x.probability,0.71)
    def test_abstain(self):
        self.assertFalse(recover_pre_settlement_probability({"x":1}).recovered)

if __name__=="__main__":
    print("="*72);print(" OLR-021 CERTIFICATION TEST");print(" PRE-SETTLEMENT PROBABILITY RECOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Defensible probability recovery certified")
    print("[PASS] Missing probability evidence causes abstention")
    print("[DONE] OLR-021 CERTIFIED")
