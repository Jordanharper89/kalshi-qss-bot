import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_226_crypto_physical_adaptive_state_and_ocl029_readmission as m
class T(unittest.TestCase):
    def test_hold(self):
        cal=SimpleNamespace(state="HOLD_HISTORICAL_FORECAST_PROBABILITY_REQUIRED");rel=SimpleNamespace(state="HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")
        mb=SimpleNamespace(market_behavior_state_hash="a"*64);mat=SimpleNamespace(maturity_state_hash="b"*64)
        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)
        with patch.object(m,"materialize_physical_calibration_state",return_value=cal),patch.object(m,"materialize_physical_source_reliability_state",return_value=rel),patch.object(m,"materialize_physical_market_behavior_state",return_value=mb),patch.object(m,"materialize_physical_maturity_state",return_value=mat),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):
            r=m.run_physical_adaptive_and_ocl029_readmission()
        print("[SUPPLIED]",r.supplied_hashes);print("[MISSING]",r.missing_state_hashes)
        self.assertIn("market_behavior_state_hash",r.supplied_hashes);self.assertIn("maturity_state_hash",r.supplied_hashes);self.assertIsNone(r.adaptive_weight_state_hash);self.assertFalse(r.handoff_verified)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-226 adaptive HOLD + OCL-029 readmission path certified")
