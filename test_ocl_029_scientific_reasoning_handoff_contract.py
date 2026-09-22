import unittest
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import *

class T(unittest.TestCase):
    def hashes(self):
        names=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
        return {n:"a"*64 for n in names}
    def test_verifier(self): self.assertTrue(verify_ocl_029_scientific_reasoning_handoff_contract())
    def test_read_only(self):
        h=build_scientific_reasoning_handoff(**self.hashes());self.assertTrue(h.read_only);self.assertFalse(h.execution_allowed)
    def test_missing(self):
        d=self.hashes();d.pop("causal_state_hash")
        with self.assertRaises(ValueError):build_scientific_reasoning_handoff(**d)

if __name__=="__main__":
    print("="*72);print(" OCL-029 CERTIFICATION TEST");print(" SCIENTIFIC REASONING HANDOFF CONTRACT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic read-only Scientific Reasoning handoff certified")
    print("[DONE] OCL-029 CERTIFIED")
