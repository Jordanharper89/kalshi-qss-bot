import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_232_crypto_prospective_empirical_forecast_foundation as m
ROWS=((1,"o","s","t",{"asset":"BTC","return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)}),
      (2,"p","s","t",{"asset":"BTC","return_fraction":-.01,"condition_vector":(("bitcoin","fee",1,"LOW"),)}),
      (3,"q","s","t",{"asset":"BTC","return_fraction":.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)}))
class T(unittest.TestCase):
    def test_forecast(self):
        snap=SimpleNamespace(as_of_sequence=3,snapshot_hash="a"*64,rows=ROWS)
        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):
            x=m.build_prospective_crypto_forecasts(created_at="2026-08-31T20:00:00+00:00")[0]
        print("[FORECAST]",x.asset,x.sample_size,x.internal_forecast_probability,"[CLAIMS]",x.source_claims)
        self.assertAlmostEqual(x.internal_forecast_probability,3/5)
        self.assertFalse(x.probability_enabled);self.assertFalse(x.publication_allowed);self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-232 prospective empirical forecast foundation certified")
