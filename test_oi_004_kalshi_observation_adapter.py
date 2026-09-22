from __future__ import annotations
import unittest
from qseries_v2.observation_intelligence.oi_004_kalshi_observation_adapter import OI_004_REVISION, KalshiUniversalObservationAdapter, verify_kalshi_observation_adapter

def fake_transport(url: str, timeout: float):
    assert "/markets?" in url and timeout > 0
    return {"markets": [
        {"ticker":"KXBTC-TEST","title":"Will Bitcoin be above $100,000?","status":"open","yes_bid":54,"yes_ask":56,"volume":1000},
        {"ticker":"KXCPI-TEST","title":"Will CPI exceed 3 percent?","status":"open","yes_bid":42,"yes_ask":44,"volume":500},
    ], "cursor":""}

class TestOI004(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_kalshi_observation_adapter())
    def test_all_categories_share_adapter(self):
        values = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()
        self.assertEqual(len(values), 2)
        self.assertEqual({item.metadata["market_ticker"] for item in values}, {"KXBTC-TEST","KXCPI-TEST"})
    def test_source(self):
        item = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()[0]
        self.assertEqual(item.source.adapter_id, "adapter.kalshi.v1")
    def test_payload(self):
        item = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()[0]
        self.assertIn("yes_bid", item.payload)
    def test_bad_status(self):
        with self.assertRaises(ValueError):
            KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets(status="bad")
    def test_side_effects(self):
        a = KalshiUniversalObservationAdapter(transport=fake_transport)
        self.assertTrue(a.read_only); self.assertTrue(a.network_allowed)
        self.assertFalse(a.persistence_allowed); self.assertFalse(a.publication_allowed)
        self.assertFalse(a.execution_allowed); self.assertFalse(a.qseries_execution_allowed)

if __name__ == "__main__":
    print("="*72); print(" OI-004 CERTIFICATION TEST"); print(" KALSHI UNIVERSAL OBSERVATION ADAPTER"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI004))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-004"); print(f"[PASS] Revision: {OI_004_REVISION}")
    print("[PASS] One Kalshi adapter supports markets across categories")
    print("[PASS] Public market snapshots normalize into OI-001 envelopes")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-004 CERTIFIED")
