import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics
class T(unittest.TestCase):
    def test_stats(self):
        def c(v): return SimpleNamespace(asset="BTC",horizon_seconds=60,condition_vector=(("bitcoin","fee",1,"HIGH"),),temporal_vector=(("bitcoin","fee","INCREASED",1,1,True),),return_percent=v)
        x=build_comparable_condition_outcome_statistics((c(1),c(2),c(-1)))[0]
        print("[SAMPLE]",x.sample_size); print("[RAW_POS_FREQ]",x.raw_positive_frequency); print("[MEAN]",x.mean_return_percent)
        self.assertEqual(x.sample_size,3); self.assertEqual(x.positive,2); self.assertFalse(x.probability_enabled)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-190 factual comparable-condition outcome statistics certified")
