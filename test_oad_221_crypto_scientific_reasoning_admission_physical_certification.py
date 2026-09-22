import unittest

from qseries_v2.oracle_adapters.independent.oad_221_crypto_scientific_reasoning_admission_physical_certification import (
    certify_crypto_scientific_reasoning_admission,
)

class T(unittest.TestCase):
    def test_physical_current_admission(self):
        r=certify_crypto_scientific_reasoning_admission()

        print("[PHYSICAL] learner_state_hash=",r.learner_state_hash)
        print("[PHYSICAL] learner_state_verified=",r.learner_state_verified)
        print("[PHYSICAL] certified_existing_contracts=",r.certified_existing_contracts)
        print("[PHYSICAL] unavailable_existing_contracts=",r.unavailable_existing_contracts)
        print("[PHYSICAL] supplied_certified_state_hashes=",r.supplied_certified_state_hashes)
        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] handoff_hash=",r.handoff_hash)
        print("[PHYSICAL] handoff_verified=",r.handoff_verified)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        print("[PHYSICAL] probability_enabled=",r.probability_enabled)
        print("[PHYSICAL] direction_enabled=",r.direction_enabled)
        print("[PHYSICAL] execution_authority=",r.execution_authority)

        self.assertTrue(r.learner_state_verified)
        self.assertTrue(r.physical_ready)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

        if r.missing_state_hashes:
            self.assertEqual(
                r.state,
                "HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED"
            )
            self.assertIsNone(r.handoff_hash)
            self.assertFalse(r.handoff_verified)
        else:
            self.assertEqual(
                r.state,
                "READY_FOR_SCIENTIFIC_REASONING_HANDOFF"
            )
            self.assertEqual(len(r.handoff_hash),64)
            self.assertTrue(r.handoff_verified)

if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-221 physical Scientific Reasoning admission truthfully certified")
