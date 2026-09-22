import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_238_crypto_prospective_learning_state_refresh as m

class T(unittest.TestCase):
    def test_exact_certified_contracts(self):
        c=SimpleNamespace(
            calibration_state_hash=None,
            source_reliability_state_hash=None,
            state="HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED",
        )
        a=SimpleNamespace(
            adaptive_weight_state_hash=None,
            adaptive_state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED",
            admission_state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",
            handoff_verified=False,
        )
        with patch.object(m,"materialize_prospective_calibration_source_reliability",return_value=c) as pc, \
             patch.object(m,"run_prospective_adaptive_ocl029_readmission",return_value=a) as pa:
            x=m.refresh_prospective_learning_states()

        print("[CALIBRATION]",x.calibration_state)
        print("[ADAPTIVE]",x.adaptive_state)
        print("[ADMISSION]",x.admission_state)
        self.assertEqual(pc.call_count,1)
        self.assertEqual(pa.call_count,1)
        self.assertIsNone(x.calibration_state_hash)
        self.assertIsNone(x.source_reliability_state_hash)
        self.assertIsNone(x.adaptive_weight_state_hash)
        self.assertFalse(x.handoff_verified)
        self.assertFalse(x.probability_enabled)
        self.assertFalse(x.direction_enabled)
        self.assertFalse(x.publication_allowed)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-238 exact certified OAD-235/OAD-236 contract refresh certified")
