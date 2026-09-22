import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_233_crypto_prospective_forecast_single_writer_persistence import canonicalize_prospective_forecast
class T(unittest.TestCase):
    def test_canonical(self):
        f=SimpleNamespace(forecast_id="a"*64,asset="BTC",created_at="2026-08-31T20:00:00+00:00",training_as_of_sequence=10,training_snapshot_hash="b"*64,sample_size=5,positive_count=3,negative_or_flat_count=2,internal_forecast_probability=.57,source_claims=(("bitcoin",5,.6,True),),horizon_seconds=60)
        x=canonicalize_prospective_forecast(f);p=dict(x.payload)
        print("[SOURCE]",x.source_id,"[P_INTERNAL]",p["internal_forecast_probability"])
        self.assertFalse(p["probability_enabled"]);self.assertFalse(p["publication_allowed"]);self.assertFalse(x.execution_allowed)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-233 prospective forecast single-writer persistence contract certified")
