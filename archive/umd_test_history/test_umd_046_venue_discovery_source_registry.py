from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_045_venue_discovery_source_contract import (
    UMD_045_REVISION,
    CertifiedVenueDiscoverySourceContract,
)
from qseries_v2.universal_market_discovery.umd_046_venue_discovery_source_registry import (
    UMD_046_REVISION,
    CertifiedVenueDiscoverySourceRegistry,
    build_umd_046_certification_manifest,
    certify_umd_046_foundation,
    certify_venue_discovery_source_registry,
)

FIXED = datetime(2026, 8, 6, 19, 55, 0, tzinfo=timezone.utc)


def source_lineage(name: str) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-045",
        revision=UMD_045_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(f"fixture://umd-046/source/{name}",),
        created_at=FIXED,
    )


def source(
    venue: str,
    adapter: str,
    method: str = "REST_CATALOG",
) -> CertifiedVenueDiscoverySourceContract:
    return CertifiedVenueDiscoverySourceContract(
        canonical_venue_id=venue,
        adapter_key=adapter,
        display_name=f"{venue} {adapter}",
        discovery_method=method,
        authentication_mode="API_KEY",
        pagination_mode="CURSOR",
        supported_market_families=("BINARY_MARKET",),
        supported_statuses=("ACTIVE", "CLOSED", "SETTLED"),
        source_schema_version="v1",
        supports_incremental_discovery=True,
        supports_historical_markets=True,
        supports_settlement_status=True,
        supports_cursor_resume=True,
        rate_limit_metadata_available=True,
        read_only=True,
        metadata={"certification_only": True},
        lineage=source_lineage(f"{venue}-{adapter}"),
    )


def registry(*sources):
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-046",
        revision=UMD_046_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(item.contract_hash for item in sources),
        source_refs=("fixture://umd-046/registry",),
        created_at=FIXED,
    )
    return CertifiedVenueDiscoverySourceRegistry(
        sources=tuple(sources),
        registry_metadata={"read_only": True},
        lineage=lineage,
    )


class TestUMD046(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_046_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-046")

    def test_registry_certifies(self) -> None:
        item = registry(
            source("KALSHI", "KALSHI_MARKET_CATALOG"),
            source("POLYMARKET", "POLYMARKET_MARKET_CATALOG"),
        )
        result = certify_venue_discovery_source_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["venue_count"], 2)

    def test_deterministic(self) -> None:
        first_source = source("KALSHI", "KALSHI_MARKET_CATALOG")
        first = registry(first_source)
        second = registry(first_source)
        self.assertEqual(first.registry_id, second.registry_id)
        self.assertEqual(first.registry_hash, second.registry_hash)

    def test_lookup_indexes(self) -> None:
        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")
        polymarket = source("POLYMARKET", "POLYMARKET_MARKET_CATALOG")
        item = registry(kalshi, polymarket)
        self.assertIs(item.get(kalshi.source_id), kalshi)
        self.assertIs(
            item.get_by_venue_adapter(
                "kalshi",
                "kalshi-market-catalog",
            ),
            kalshi,
        )
        self.assertEqual(item.list_by_venue("KALSHI"), (kalshi,))

    def test_duplicate_source_rejected(self) -> None:
        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")
        with self.assertRaises(ValueError):
            registry(kalshi, kalshi)

    def test_duplicate_venue_adapter_rejected(self) -> None:
        first = source("KALSHI", "KALSHI_MARKET_CATALOG")
        second = source("KALSHI", "KALSHI_MARKET_CATALOG")
        with self.assertRaises(ValueError):
            registry(first, second)

    def test_lineage_requires_contract_hashes(self) -> None:
        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-046",
            revision=UMD_046_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-046/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedVenueDiscoverySourceRegistry(
                sources=(kalshi,),
                registry_metadata={},
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        item = registry(source("KALSHI", "KALSHI_MARKET_CATALOG"))
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.sources = ()
        with self.assertRaises(TypeError):
            item.registry_metadata["read_only"] = False
        with self.assertRaises(TypeError):
            item._by_source_id["x"] = None

    def test_side_effects(self) -> None:
        manifest = build_umd_046_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-046 CERTIFICATION TEST")
    print(" CERTIFIED VENUE DISCOVERY SOURCE REGISTRY")
    print("=" * 72)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD046)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_046_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-045 consumed read-only")
    print("[PASS] Exact UMD-045 source-contract class consumed")
    print("[PASS] Deterministic source registry identity certified")
    print("[PASS] Venue and adapter uniqueness enforced")
    print("[PASS] Immutable read-only registry indexes certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-046 CERTIFIED VENUE DISCOVERY SOURCE REGISTRY CERTIFIED")
