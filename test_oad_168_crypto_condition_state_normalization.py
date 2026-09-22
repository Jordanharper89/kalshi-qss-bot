import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states
class T(unittest.TestCase):
    def test_normalize(self):
        metrics=(
            SimpleNamespace(asset="BTC",source_family="coinbase",metric_name="bid_ask_spread_bps",value=2.0,unit="bps",independent_evidence=False,market_native_reference=True,observed_at=None),
            SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",value=60.0,unit="sat/vB",independent_evidence=True,market_native_reference=False,observed_at=None),
            SimpleNamespace(asset="BTC",source_family="coinbase",metric_name="spot_price",value=60000.0,unit="USD",independent_evidence=False,market_native_reference=True,observed_at=None),
        )
        r=normalize_crypto_condition_states(metrics)
        print("[CONDITIONS]",tuple((x.metric_name,x.condition) for x in r))
        self.assertEqual(r[0].condition,"TIGHT")
        self.assertEqual(r[1].condition,"HIGH")
        self.assertEqual(r[2].condition,"OBSERVED")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-168 crypto condition normalization certified")
