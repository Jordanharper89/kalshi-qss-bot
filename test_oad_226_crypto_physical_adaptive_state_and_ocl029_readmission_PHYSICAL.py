import unittest
from qseries_v2.oracle_adapters.independent.oad_226_crypto_physical_adaptive_state_and_ocl029_readmission import run_physical_adaptive_and_ocl029_readmission
class T(unittest.TestCase):
    def test_physical(self):
        r=run_physical_adaptive_and_ocl029_readmission()
        print("[PHYSICAL] calibration_state=",r.calibration_state)
        print("[PHYSICAL] source_reliability_state=",r.source_reliability_state)
        print("[PHYSICAL] market_behavior_state_hash=",r.market_behavior_state_hash)
        print("[PHYSICAL] maturity_state_hash=",r.maturity_state_hash)
        print("[PHYSICAL] adaptive_state=",r.adaptive_state)
        print("[PHYSICAL] supplied_hashes=",r.supplied_hashes)
        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)
        print("[PHYSICAL] admission_state=",r.admission_state)
        print("[PHYSICAL] handoff_verified=",r.handoff_verified)
        print("[PHYSICAL] probability_enabled=",r.probability_enabled)
        print("[PHYSICAL] direction_enabled=",r.direction_enabled)
        print("[PHYSICAL] execution_authority=",r.execution_authority)
        self.assertTrue(r.physical_ready);self.assertFalse(r.probability_enabled);self.assertFalse(r.direction_enabled);self.assertFalse(r.execution_authority)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-226 physical materialization I + OCL-029 readmission certified")
