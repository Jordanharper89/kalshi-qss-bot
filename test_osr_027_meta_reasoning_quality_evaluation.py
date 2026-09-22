import unittest
from qseries_v2.oracle_scientific_reasoning.osr_027_meta_reasoning_quality import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_027_meta_reasoning_quality_evaluation())

    def test_abstain(self):
        x = ReasoningQualityInput("x", 0.1, 0.1, 0.1, 0.1)
        self.assertTrue(evaluate_reasoning_quality(x).abstain)

    def test_weakest(self):
        x = ReasoningQualityInput("x", 1.0, 0.2, 0.8, 0.9)
        self.assertEqual(evaluate_reasoning_quality(x).weakest_dimension, "contradiction_control")

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-027 CERTIFICATION TEST")
    print(" META-REASONING + REASONING-QUALITY EVALUATION")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Meta-reasoning quality evaluation with abstention certified")
    print("[DONE] OSR-027 CERTIFIED")
