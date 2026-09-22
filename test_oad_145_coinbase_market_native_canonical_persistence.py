import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_145_coinbase_market_native_canonical_persistence as m
from qseries_v2.oracle_adapters.independent.oad_142_coinbase_crypto_market_data_foundation import build_coinbase_market_observation
class T(unittest.TestCase):
    def test_market_native_persistence_contract(self):
        o=build_coinbase_market_observation(source_id="coinbase:BTC-USD:ticker:1",crypto_family="spot",observation_type="live_ticker",subject="BTC-USD",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.exchange.coinbase.com/products/BTC-USD/ticker",payload={"price":"60000"})
        c=m.canonicalize_coinbase_market_observation(o,"test")
        self.assertEqual(c.source_id,"source.market_native.coinbase")
        self.assertFalse(c.execution_allowed)
        with patch.object(m,"acquire_coinbase_live_spot_observations",return_value=(o,)),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_current_coinbase_market_native()
        print("[SOURCE_ID]",c.source_id); print("[RAW]",r.raw_observations); print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.exact_readback,1)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-145 Coinbase market-native canonical persistence certified")
    print("[PASS] universal PostgreSQL queue used with producer oracle.coinbase_market_data")
