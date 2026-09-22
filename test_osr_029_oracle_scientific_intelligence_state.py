import unittest
from qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import CapabilityReasoningState, synthesize_capabilities
from qseries_v2.oracle_scientific_reasoning.osr_029_intelligence_state import *

class T(unittest.TestCase):
    def synthesis(self):
        return synthesize_capabilities(
            (CapabilityReasoningState("scientific", 0.9, 0.9, 0.1, False),)
        )

    def test_verifier(self):
        self.assertTrue(verify_osr_029_oracle_scientific_intelligence_state())

    def test_read_only(self):
        x = build_oracle_scientific_intelligence_state("subject", self.synthesis())
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_allowed)
        self.assertFalse(x.publication_allowed)

    def test_subject_required(self):
        with self.assertRaises(ValueError):
            build_oracle_scientific_intelligence_state("", self.synthesis())

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-029 CERTIFICATION TEST")
    print(" ORACLE SCIENTIFIC INTELLIGENCE STATE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Canonical read-only Oracle scientific intelligence state certified")
    print("[DONE] OSR-029 CERTIFIED")
