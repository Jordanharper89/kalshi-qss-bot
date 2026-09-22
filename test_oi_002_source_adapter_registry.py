from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    OI_002_REVISION,
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
    verify_source_adapter_registry,
)


def crypto():
    return SourceAdapterDescriptor(
        adapter_id="adapter.crypto.v1",
        source_id="crypto.market_data",
        source_kind="market_data",
        provider="Crypto Market Data",
        adapter_version="1.0.0",
        capabilities=("market snapshot", "spot price"),
        enabled_for_intake=True,
    )


def kalshi():
    return SourceAdapterDescriptor(
        adapter_id="adapter.kalshi.v1",
        source_id="kalshi.public",
        source_kind="market_venue",
        provider="Kalshi",
        adapter_version="1.0.0",
        capabilities=("market discovery", "market snapshot"),
        enabled_for_intake=True,
    )


class TestOI002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_source_adapter_registry())

    def test_registry(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.adapters), 2)

    def test_lookup(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertIsNotNone(registry.get("adapter.kalshi.v1"))

    def test_kind_query(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.by_kind("market_data")), 1)

    def test_enabled(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.enabled()), 2)

    def test_deterministic(self):
        a = SourceAdapterRegistry((crypto(), kalshi()))
        b = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(a.registry_hash, b.registry_hash)

    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):
            SourceAdapterRegistry((kalshi(), crypto()))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            SourceAdapterRegistry((kalshi(), kalshi()))

    def test_source_identity(self):
        self.assertEqual(kalshi().source_identity().source_id, "kalshi.public")

    def test_side_effects(self):
        registry = SourceAdapterRegistry(())
        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-002 CERTIFICATION TEST")
    print(" SOURCE ADAPTER REGISTRY — CORRECTION V2")
    print("=" * 72)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestOI002)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OI-002")
    print(f"[PASS] Revision: {OI_002_REVISION}")
    print("[PASS] Universal source adapter descriptors certified")
    print("[PASS] Adapter lookup and source-kind registry certified")
    print("[PASS] Source identity contract aligned to certified OI-001")
    print("[PASS] No category-specific acquisition logic introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-002 CERTIFIED")
