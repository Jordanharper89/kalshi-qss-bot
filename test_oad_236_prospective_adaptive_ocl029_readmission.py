import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_236_prospective_adaptive_ocl029_readmission as m
class T(unittest.TestCase):
    def test_hold_without_future_case(self):
        cr=SimpleNamespace(calibration_state_hash=None,source_reliability_state_hash=None)
        bm=SimpleNamespace(market_behavior_state_hash="a"*64,maturity_state_hash="b"*64,maturity_score=0.0)
        er=SimpleNamespace(entity_relationship_state_hash="c"*64);cn=SimpleNamespace()
        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","causal_state_hash","narrative_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)
        with patch.object(m,"read_and_score_mature_prospective_cases",return_value=()),patch.object(m,"materialize_prospective_calibration_source_reliability",return_value=cr),patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):
            r=m.run_prospective_adaptive_ocl029_readmission()
        print("[STATE]",r.adaptive_state,"[MISSING]",r.missing_state_hashes)
        self.assertIsNone(r.adaptive_weight_state_hash);self.assertFalse(r.handoff_verified)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-236 prospective adaptive + OCL-029 readmission contract certified")
