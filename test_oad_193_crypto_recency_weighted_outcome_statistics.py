import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_193_crypto_recency_weighted_outcome_statistics import build_recency_weighted_outcome_statistics
class T(unittest.TestCase):
    def test_recency(self):
        def c(ts,v):
            return SimpleNamespace(asset="BTC",horizon_seconds=60,
                condition_vector=(("bitcoin","fee",1,"HIGH"),),
                temporal_vector=(("bitcoin","fee","INCREASED",1,1,True),),
                outcome_observed_at=ts,return_percent=v)
        rows=build_recency_weighted_outcome_statistics(
            (c("2026-08-29T00:00:00+00:00",-1.0),c("2026-08-30T00:00:00+00:00",2.0)),
            reference_time="2026-08-30T00:00:00+00:00",half_life_seconds=86400
        )
        x=rows[0]
        print("[RAW_N]",x.raw_sample_size); print("[ESS]",x.effective_sample_size); print("[WEIGHTED_POS_SHARE]",x.weighted_positive_share)
        self.assertEqual(x.raw_sample_size,2)
        self.assertGreater(x.weighted_positive_share,0.5)
        self.assertFalse(x.probability_enabled)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-193 recency-weighted descriptive outcome statistics certified")
