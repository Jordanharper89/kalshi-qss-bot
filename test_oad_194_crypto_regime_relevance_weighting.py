import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_194_crypto_regime_relevance_weighting import build_regime_relevance_weighted_profile
class T(unittest.TestCase):
    def test_regime(self):
        def c(e,state,trend,ts,v):
            return SimpleNamespace(asset="BTC",horizon_seconds=60,experience_id=e,
                condition_vector=(("bitcoin","fee",1,state),),
                temporal_vector=(("bitcoin","fee",trend,1,1,True),),
                outcome_observed_at=ts,return_percent=v)
        ref=c("new","HIGH","INCREASED","2026-08-30T00:00:00+00:00",2)
        old_same=c("same","HIGH","INCREASED","2026-08-29T00:00:00+00:00",1)
        old_diff=c("diff","LOW","DECREASED","2026-08-29T00:00:00+00:00",-1)
        x=build_regime_relevance_weighted_profile(ref,(old_same,old_diff),reference_time="2026-08-30T00:00:00+00:00",half_life_seconds=86400)
        print("[CASES]",x.historical_case_count); print("[MEAN_SIM]",x.mean_regime_similarity); print("[ESS]",x.effective_sample_size)
        self.assertEqual(x.historical_case_count,2)
        self.assertGreater(x.weighted_positive_share,x.weighted_negative_share)
        self.assertFalse(x.probability_enabled)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-194 regime-similarity + recency relevance weighting certified")
