import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics

class T(unittest.TestCase):
    def test_extract(self):
        obs=(
            ("coinbase",SimpleNamespace(subject="BTC-USD",observation_type="live_ticker",observed_at="2026-08-29T00:00:00+00:00",payload={"base_currency":"BTC","price":"60000","volume":"123","bid":"59999","ask":"60001"})),
            ("bitcoin",SimpleNamespace(subject="btc",observation_type="mempool_pressure",observed_at="2026-08-29T00:00:01+00:00",payload={"count":1000,"vsize":2000000,"recommended_fees":{"fastestFee":10,"halfHourFee":8}})),
        )
        r=extract_crypto_condition_metrics(SimpleNamespace(observations=obs))
        names=tuple(x.metric_name for x in r)
        print("[METRICS]",names)
        self.assertIn("spot_price",names)
        self.assertIn("bid_ask_spread_bps",names)
        self.assertIn("mempool_transaction_count",names)
        self.assertTrue(any(x.market_native_reference for x in r))
        self.assertTrue(any(x.independent_evidence for x in r))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-167 structured crypto metric extraction certified")
