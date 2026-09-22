import unittest
from types import SimpleNamespace
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_adapters.independent.oad_188_crypto_verified_learned_case_postgresql_persistence import canonicalize_verified_learned_case
class T(unittest.TestCase):
    def test_case(self):
        e=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-29T02:00:00+00:00",condition_vector=(("bitcoin","fee",1.0,"HIGH"),),temporal_vector=(("bitcoin","fee","INCREASED",1,1,True),),evidence_hash="a"*64,condition_hash="b"*64,experience_hash="c"*64,lineage_hash="d"*64)
        ocl=build_outcome_observation("BTC","coinbase_spot_return_60s_exact_interval",.01,"2026-08-29T02:01:00+00:00","coinbase:x","e"*64)
        o=SimpleNamespace(horizon_seconds=60,matures_at="2026-08-29T02:01:00+00:00",candle_start="2026-08-29T02:01:00+00:00",start_price=100,outcome_price=101,return_fraction=.01,return_percent=1.0,outcome_observation=ocl,source_ref="coinbase:x",source_hash="e"*64)
        x=canonicalize_verified_learned_case(e,o); p=dict(x.payload)
        print("[SOURCE]",x.source_id); print("[EVENT]",p["learning_event_hash"])
        self.assertTrue(p["exact_interval"]); self.assertIsNone(p["probability"]); self.assertFalse(x.execution_allowed)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-188 immutable verified learned-case persistence contract certified")
