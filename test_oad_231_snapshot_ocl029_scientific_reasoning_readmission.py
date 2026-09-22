import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_231_snapshot_ocl029_scientific_reasoning_readmission as m
class T(unittest.TestCase):
    def test_snapshot_readmission(self):
        bm=SimpleNamespace(as_of_sequence=50,market_behavior_state_hash="a"*64,maturity_state_hash="b"*64)
        er=SimpleNamespace(as_of_sequence=50,entity_relationship_state_hash="c"*64)
        cn=SimpleNamespace(as_of_sequence=50,causal_state="HOLD_EXPLICIT_CAUSAL_EVIDENCE_REQUIRED",narrative_state="HOLD_EXPLICIT_NARRATIVE_EVIDENCE_REQUIRED")
        cal=SimpleNamespace(state="HOLD_HISTORICAL_FORECAST_PROBABILITY_REQUIRED")
        rel=SimpleNamespace(state="HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")
        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","causal_state_hash","narrative_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)
        with patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn),patch.object(m,"materialize_physical_calibration_state",return_value=cal),patch.object(m,"materialize_physical_source_reliability_state",return_value=rel),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):
            r=m.run_snapshot_ocl029_readmission()
        print("[SUPPLIED]",r.supplied_hashes);print("[MISSING]",r.missing_state_hashes)
        self.assertEqual(r.supplied_hashes,("entity_relationship_state_hash","market_behavior_state_hash","maturity_state_hash"))
        self.assertFalse(r.handoff_verified)

    def test_cross_snapshot_rejected(self):
        bm=SimpleNamespace(as_of_sequence=50,market_behavior_state_hash="a"*64,maturity_state_hash="b"*64)
        er=SimpleNamespace(as_of_sequence=51,entity_relationship_state_hash="c"*64)
        cn=SimpleNamespace(as_of_sequence=50,causal_state="",narrative_state="")
        with patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn):
            with self.assertRaises(RuntimeError):m.run_snapshot_ocl029_readmission()

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-231 same-snapshot OCL-029 readmission contract certified")
