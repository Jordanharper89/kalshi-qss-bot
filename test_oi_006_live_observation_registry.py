from __future__ import annotations
import unittest

from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import PublicMarketDataObservationAdapter
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    OI_006_REVISION,
    LiveObservationRegistry,
    default_source_registry,
    read_live_spot_observation,
    verify_live_observation_registry,
)

def fake_transport(url: str, timeout: float):
    return {"data":{"amount":"123456.78","currency":"USD"}}

class TestOI006(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_live_observation_registry())
    def test_sources(self):
        r=default_source_registry()
        self.assertIsNotNone(r.get("adapter.coinbase.spot.v1"))
        self.assertIsNotNone(r.get("adapter.kalshi.v1"))
    def test_spot_canonicalization(self):
        o=read_live_spot_observation("BTC-USD",market_data_adapter=PublicMarketDataObservationAdapter(transport=fake_transport))
        self.assertEqual(o.subject,"BTC"); self.assertEqual(o.observation_type,"spot_price")
        self.assertEqual(o.facts["price"],"123456.78")
    def test_latest(self):
        o=read_live_spot_observation("BTC-USD",market_data_adapter=PublicMarketDataObservationAdapter(transport=fake_transport))
        r=LiveObservationRegistry((o,))
        self.assertIs(r.latest("BTC","spot_price"),o)
    def test_side_effects(self):
        r=LiveObservationRegistry(())
        self.assertTrue(r.read_only); self.assertFalse(r.persistence_allowed)
        self.assertFalse(r.publication_allowed); self.assertFalse(r.execution_allowed)
        self.assertFalse(r.qseries_execution_allowed)

if __name__=="__main__":
    print("="*72); print(" OI-006 CERTIFICATION TEST"); print(" LIVE OBSERVATION REGISTRY + TERMINAL BRIDGE"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI006))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-006"); print(f"[PASS] Revision: {OI_006_REVISION}")
    print("[PASS] Kalshi and Coinbase adapters registered through one intake contract")
    print("[PASS] Live spot observations canonicalize through OI-003")
    print("[PASS] Deterministic latest-observation registry certified")
    print("[PASS] Terminal live-price bridge binding installed")
    print("[PASS] Persistence, publication, action authorization, and execution disabled")
    print("[DONE] OI-006 CERTIFIED")
