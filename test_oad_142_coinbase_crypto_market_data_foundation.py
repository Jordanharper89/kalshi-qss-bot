import unittest
from qseries_v2.oracle_adapters.independent.oad_142_coinbase_crypto_market_data_foundation import build_coinbase_market_observation,validate_coinbase_market_observation
class T(unittest.TestCase):
    def test_market_native_not_independent(self):
        o=build_coinbase_market_observation(source_id="coinbase:BTC-USD:ticker",crypto_family="spot",observation_type="ticker",subject="BTC-USD",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.exchange.coinbase.com/products/BTC-USD/ticker",payload={"price":"60000"})
        self.assertTrue(validate_coinbase_market_observation(o))
        self.assertFalse(o.independent_evidence); self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-142 Coinbase crypto market-data foundation certified")
    print("[PASS] Coinbase classified market_native_reference independent_evidence=FALSE")
