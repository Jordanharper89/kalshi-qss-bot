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
    build_umd_045_certification_manifest,
    certify_umd_045_foundation,
    certify_venue_discovery_source_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    19,
    45,
    0,
    tzinfo=timezone.utc,
)


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-045",
        revision=UMD_045_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(
            "fixture://umd-045/source-contract",
        ),
        created_at=FIXED,
    )


def source_contract() -> CertifiedVenueDiscoverySourceContract:
    return CertifiedVenueDiscoverySourceContract(
        canonical_venue_id="KALSHI",
        adapter_key="KALSHI_MARKET_CATALOG",
        display_name="Kalshi Market Catalog",
        discovery_method="REST_CATALOG",
        authentication_mode="API_KEY",
        pagination_mode="CURSOR",
        supported_market_families=(
            "EVENT_CONTRACT",
            "BINARY_MARKET",
        ),
        supported_statuses=(
            "ACTIVE",
            "CLOSED",
            "SETTLED",
        ),
        source_schema_version="kalshi-market-catalog-v1",
        supports_incremental_discovery=True,
        supports_historical_markets=True,
        supports_settlement_status=True,
        supports_cursor_resume=True,
        rate_limit_metadata_available=True,
        read_only=True,
        metadata={
            "network_enabled": False,
            "certification_only": True,
        },
        lineage=lineage(),
    )


class TestUMD045(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_045_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-045")

    def test_contract_certifies(self) -> None:
        source = source_contract()
        result = certify_venue_discovery_source_contract(source)
        self.assertTrue(result["certified"])
        self.assertEqual(
            result["canonical_venue_id"],
            "KALSHI",
        )

    def test_deterministic_identity(self) -> None:
        first = source_contract()
        second = source_contract()
        self.assertEqual(first.source_id, second.source_id)
        self.assertEqual(
            first.contract_hash,
            second.contract_hash,
        )

    def test_normalization(self) -> None:
        source = CertifiedVenueDiscoverySourceContract(
            canonical_venue_id="kalshi",
            adapter_key="kalshi-market-catalog",
            display_name="  Kalshi   Market Catalog ",
            discovery_method="rest-catalog",
            authentication_mode="api-key",
            pagination_mode="cursor",
            supported_market_families=(
                "binary-market",
                "event-contract",
                "binary-market",
            ),
            supported_statuses=(
                "settled",
                "active",
                "closed",
            ),
            source_schema_version="v1",
            supports_incremental_discovery=True,
            supports_historical_markets=True,
            supports_settlement_status=True,
            supports_cursor_resume=True,
            rate_limit_metadata_available=True,
            read_only=True,
            metadata={},
            lineage=lineage(),
        )
        self.assertEqual(source.canonical_venue_id, "KALSHI")
        self.assertEqual(
            source.supported_market_families,
            ("BINARY_MARKET", "EVENT_CONTRACT"),
        )
        self.assertEqual(
            source.supported_statuses,
            ("ACTIVE", "CLOSED", "SETTLED"),
        )

    def test_cursor_resume_requires_cursor_mode(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedVenueDiscoverySourceContract(
                canonical_venue_id="TEST",
                adapter_key="TEST_SOURCE",
                display_name="Test Source",
                discovery_method="REST_CATALOG",
                authentication_mode="NONE",
                pagination_mode="OFFSET",
                supported_market_families=(
                    "BINARY_MARKET",
                ),
                supported_statuses=("ACTIVE",),
                source_schema_version="v1",
                supports_incremental_discovery=True,
                supports_historical_markets=False,
                supports_settlement_status=False,
                supports_cursor_resume=True,
                rate_limit_metadata_available=False,
                read_only=True,
                metadata={},
                lineage=lineage(),
            )

    def test_read_only_required(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedVenueDiscoverySourceContract(
                canonical_venue_id="TEST",
                adapter_key="TEST_SOURCE",
                display_name="Test Source",
                discovery_method="FILE_CATALOG",
                authentication_mode="NONE",
                pagination_mode="NONE",
                supported_market_families=(
                    "BINARY_MARKET",
                ),
                supported_statuses=("ACTIVE",),
                source_schema_version="v1",
                supports_incremental_discovery=False,
                supports_historical_markets=False,
                supports_settlement_status=False,
                supports_cursor_resume=False,
                rate_limit_metadata_available=False,
                read_only=False,
                metadata={},
                lineage=lineage(),
            )

    def test_immutable(self) -> None:
        source = source_contract()
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            source.display_name = "Changed"
        with self.assertRaises(TypeError):
            source.metadata["network_enabled"] = True

    def test_side_effects(self) -> None:
        manifest = build_umd_045_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-045 CERTIFICATION TEST")
    print(" CERTIFIED VENUE DISCOVERY SOURCE CONTRACT")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD045
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_045_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-044 consumed read-only")
    print("[PASS] Deterministic venue discovery source identity certified")
    print("[PASS] Supported families and statuses normalized")
    print("[PASS] Authentication and pagination capabilities certified")
    print("[PASS] Read-only source definition enforced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-045 CERTIFIED VENUE DISCOVERY SOURCE CONTRACT CERTIFIED")
