import unittest
from qseries_v2.oracle_adapters.independent.oad_236_prospective_adaptive_ocl029_readmission import run_prospective_adaptive_ocl029_readmission
class T(unittest.TestCase):
    def test_physical(self):
        r=run_prospective_adaptive_ocl029_readmission()
        print("[PHYSICAL] scored_cases=",r.scored_cases)
        print("[PHYSICAL] adaptive_state=",r.adaptive_state)
        print("[PHYSICAL] adaptive_weight_state_hash=",r.adaptive_weight_state_hash)
        print("[PHYSICAL] supplied_hashes=",r.supplied_hashes)
        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)
        print("[PHYSICAL] admission_state=",r.admission_state)
        print("[PHYSICAL] handoff_verified=",r.handoff_verified)
        print("[PHYSICAL] probability_enabled=",r.probability_enabled)
        print("[PHYSICAL] direction_enabled=",r.direction_enabled)
        print("[PHYSICAL] publication_allowed=",r.publication_allowed)
        print("[PHYSICAL] execution_authority=",r.execution_authority)
        self.assertFalse(r.probability_enabled);self.assertFalse(r.direction_enabled);self.assertFalse(r.publication_allowed);self.assertFalse(r.execution_authority)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-236 physical prospective adaptive + OCL-029 readmission certified")
