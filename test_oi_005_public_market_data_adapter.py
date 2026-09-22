from __future__ import annotations
import unittest
from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import OI_005_REVISION, PublicMarketDataObservationAdapter, verify_public_market_data_adapter

def fake_transport(url: str, timeout: float):
    assert url.endswith("/spot") and timeout > 0
    amount = "123456.78" if "BTC-USD" in url else ("5000.12" if "ETH-USD" in url else "250.50")
    return {"data":{"amount":amount,"currency":"USD"}}

class TestOI005(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_public_market_data_adapter())
    def test_btc(self):
        item=PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("BTC-USD")
        self.assertEqual(item.subject,"BTC"); self.assertEqual(item.observation_type,"spot_price")
        self.assertEqual(item.payload["price"],"123456.78")
    def test_eth(self): self.assertEqual(PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("ETH-USD").subject,"ETH")
    def test_sol(self): self.assertEqual(PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("SOL-USD").subject,"SOL")
    def test_unsupported(self):
        with self.assertRaises(ValueError): PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("DOGE-USD")
    def test_source(self):
        item=PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("BTC-USD")
        self.assertEqual(item.source.provider,"Coinbase"); self.assertEqual(item.source.adapter_id,"adapter.coinbase.spot.v1")
    def test_side_effects(self):
        a=PublicMarketDataObservationAdapter(transport=fake_transport)
        self.assertTrue(a.read_only); self.assertTrue(a.network_allowed)
        self.assertFalse(a.persistence_allowed); self.assertFalse(a.publication_allowed)
        self.assertFalse(a.execution_allowed); self.assertFalse(a.qseries_execution_allowed)

if __name__=="__main__":
    print("="*72); print(" OI-005 CERTIFICATION TEST"); print(" PUBLIC MARKET DATA ADAPTER"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI005))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-005"); print(f"[PASS] Revision: {OI_005_REVISION}")
    print("[PASS] BTC, ETH, and SOL spot observations certified through one adapter")
    print("[PASS] Public market-data observations normalize into OI-001 envelopes")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-005 CERTIFIED")
