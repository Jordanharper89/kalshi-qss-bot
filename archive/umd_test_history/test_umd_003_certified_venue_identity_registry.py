from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_venue_identity_registry import (
    UMD_003_REVISION,
    CertifiedVenueIdentity,
    ReadOnlyVenueIdentityRegistry,
    VenueOperationalStatus,
    VenueType,
    build_umd_003_certification_manifest,
    certify_umd_003_foundation,
    certify_venue_registry,
    verify_umd_003_certified_venue_identity_registry,
)

FIXED = datetime(2026, 8, 5, 5, 0, tzinfo=timezone.utc)

def lineage(source="fixture://umd-003/venue", parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-003",
        revision=UMD_003_REVISION,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(source,),
        created_at=FIXED,
    )

def venue(
    namespace="fixture-venue",
    canonical_name="Fixture Venue",
    native_namespace="fixture",
    aliases=("Fixture",),
    jurisdiction="US",
    related=(),
):
    return CertifiedVenueIdentity(
        venue_namespace=namespace,
        canonical_name=canonical_name,
        display_name=canonical_name,
        venue_type=VenueType.PREDICTION_MARKET,
        operational_status=VenueOperationalStatus.ACTIVE,
        jurisdiction=jurisdiction,
        timezone_name="America/Chicago",
        native_market_namespace=native_namespace,
        aliases=aliases,
        supported_asset_classes=("prediction_market", "politics"),
        supported_market_types=("binary", "categorical"),
        supported_currencies=("USD",),
        settlement_capabilities=("cash", "venue_determined"),
        related_venue_ids=related,
        metadata={"read_only": True},
        lineage=lineage(source=f"fixture://umd-003/{namespace}"),
    )

class TestUMD003(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_003_foundation()["certified"])
        self.assertTrue(verify_umd_003_certified_venue_identity_registry())

    def test_venue_identity_deterministic(self):
        self.assertEqual(
            venue().canonical_venue_id,
            venue().canonical_venue_id,
        )
        changed_name = venue(canonical_name="Different Display Identity")
        self.assertEqual(
            venue().canonical_venue_id,
            changed_name.canonical_venue_id,
        )
        changed_namespace = venue(namespace="other-venue")
        self.assertNotEqual(
            venue().canonical_venue_id,
            changed_namespace.canonical_venue_id,
        )

    def test_record_hash_deterministic(self):
        self.assertEqual(venue().record_hash, venue().record_hash)

    def test_duplicate_fingerprint_deterministic(self):
        first = venue()
        second = venue(namespace="other", native_namespace="other")
        self.assertEqual(
            first.duplicate_fingerprint,
            second.duplicate_fingerprint,
        )

    def test_immutable(self):
        item = venue()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.display_name = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        first = venue()
        second = venue(
            namespace="fixture-venue-two",
            canonical_name="Fixture Venue Two",
            native_namespace="fixture-two",
            aliases=("Fixture Two",),
            jurisdiction="GB",
        )
        registry = ReadOnlyVenueIdentityRegistry(
            venues=(second, first),
            registry_lineage=lineage("fixture://umd-003/registry"),
        )
        result = certify_venue_registry(registry)
        self.assertTrue(result.certified)
        self.assertEqual(result.venue_count, 2)

    def test_alias_resolution(self):
        item = venue()
        registry = ReadOnlyVenueIdentityRegistry(
            venues=(item,),
            registry_lineage=lineage("fixture://umd-003/registry"),
        )
        self.assertEqual(
            registry.resolve_alias("fixture").canonical_venue_id,
            item.canonical_venue_id,
        )
        self.assertEqual(
            registry.resolve_alias("FIXTURE VENUE").canonical_venue_id,
            item.canonical_venue_id,
        )
        self.assertIsNone(registry.resolve_alias("missing"))

    def test_ambiguous_alias_rejected(self):
        first = venue()
        second = venue(
            namespace="other-venue",
            canonical_name="Other Venue",
            native_namespace="other",
            aliases=("Fixture",),
            jurisdiction="GB",
        )
        with self.assertRaises(ValueError):
            ReadOnlyVenueIdentityRegistry(
                venues=(first, second),
                registry_lineage=lineage("fixture://umd-003/registry"),
            )

    def test_duplicate_fingerprint_rejected(self):
        first = venue()
        second = venue(
            namespace="other-venue",
            canonical_name="Fixture Venue",
            native_namespace="other",
            aliases=("Other Fixture",),
        )
        with self.assertRaises(ValueError):
            ReadOnlyVenueIdentityRegistry(
                venues=(first, second),
                registry_lineage=lineage("fixture://umd-003/registry"),
            )

    def test_self_reference_rejected(self):
        item = venue()
        with self.assertRaises(ValueError):
            venue(related=(item.canonical_venue_id,))

    def test_filters_are_deterministic(self):
        first = venue()
        second = venue(
            namespace="fixture-venue-two",
            canonical_name="Fixture Venue Two",
            native_namespace="fixture-two",
            aliases=("Fixture Two",),
            jurisdiction="GB",
        )
        registry = ReadOnlyVenueIdentityRegistry(
            venues=(second, first),
            registry_lineage=lineage("fixture://umd-003/registry"),
        )
        self.assertEqual(len(registry.by_type(VenueType.PREDICTION_MARKET)), 2)
        self.assertEqual(len(registry.by_jurisdiction("US")), 1)

    def test_side_effects_disabled(self):
        manifest = build_umd_003_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-003 CERTIFICATION TEST")
    print(" CERTIFIED VENUE IDENTITY REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD003)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_003_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 and UMD-002 consumed read-only")
    print("[PASS] Canonical Venue ID deterministic")
    print("[PASS] Venue namespace identity binding verified")
    print("[PASS] Venue contract immutable")
    print("[PASS] Alias resolution deterministic")
    print("[PASS] Ambiguous aliases rejected")
    print("[PASS] Duplicate venue identities rejected")
    print("[PASS] Read-only venue registry certified")
    print("[PASS] Network and live scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-003 CERTIFIED VENUE IDENTITY REGISTRY CERTIFIED")
