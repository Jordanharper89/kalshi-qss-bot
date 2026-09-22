import unittest
from qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_028_cross_capability_scientific_reasoning_synthesis())

    def test_contradiction_abstains(self):
        x = CapabilityReasoningState("x", 1.0, 1.0, 0.8, False)
        self.assertTrue(synthesize_capabilities((x,)).abstain)

    def test_deterministic(self):
        a = CapabilityReasoningState("a", 0.8, 0.8, 0.1, False)
        b = CapabilityReasoningState("b", 0.9, 0.9, 0.1, False)
        self.assertEqual(
            synthesize_capabilities((a, b)).synthesis_hash,
            synthesize_capabilities((b, a)).synthesis_hash,
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-028 CERTIFICATION TEST")
    print(" CROSS-CAPABILITY SCIENTIFIC REASONING SYNTHESIS")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Deterministic cross-capability reasoning synthesis certified")
    print("[DONE] OSR-028 CERTIFIED")
