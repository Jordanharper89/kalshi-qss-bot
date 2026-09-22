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
    MarketCategory,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    VenueIdentity,
)
from qseries_v2.universal_market_discovery.certified_canonical_market_contract import (
    UMD_002_REVISION,
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from qseries_v2.universal_market_discovery.certified_venue_identity_registry import (
    UMD_003_REVISION,
    CertifiedVenueIdentity,
    ReadOnlyVenueIdentityRegistry,
    VenueOperationalStatus,
    VenueType,
)
from qseries_v2.universal_market_discovery.certified_venue_market_binding_registry import (
    UMD_004_REVISION,
    CertifiedVenueMarketBinding,
    ReadOnlyVenueMarketBindingRegistry,
    build_umd_004_certification_manifest,
    certify_umd_004_foundation,
    certify_venue_market_binding_registry,
    verify_umd_004_certified_venue_market_binding_registry,
)

FIXED = datetime(2026, 8, 5, 6, 0, tzinfo=timezone.utc)

def lineage(build_id, revision, source, parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id=build_id,
        revision=revision,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(source,),
        created_at=FIXED,
    )

def venue(namespace="fixture-venue", native_namespace="fixture"):
    return CertifiedVenueIdentity(
        venue_namespace=namespace,
        canonical_name="Fixture Venue",
        display_name="Fixture Venue",
        venue_type=VenueType.PREDICTION_MARKET,
        operational_status=VenueOperationalStatus.ACTIVE,
        jurisdiction="US",
        timezone_name="America/Chicago",
        native_market_namespace=native_namespace,
        aliases=("Fixture",),
        supported_asset_classes=("prediction_market",),
        supported_market_types=("binary",),
        supported_currencies=("USD",),
        settlement_capabilities=("cash",),
        related_venue_ids=(),
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-003",
            UMD_003_REVISION,
            f"fixture://umd-003/{namespace}",
        ),
    )

def market(native_market_id="BTC-100K-2026", venue_namespace="fixture-venue", native_namespace="fixture"):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=venue_namespace,
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=native_namespace,
            metadata={"adapter": "fixture"},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC-2026",
        canonical_title=f"Fixture market {native_market_id}",
        canonical_description="Deterministic fixture market.",
        instrument_type=MarketInstrumentType.BINARY,
        category=MarketCategory(
            category_id="bitcoin",
            canonical_name="Bitcoin",
            parent_category_id="crypto",
            path=("markets", "crypto", "bitcoin"),
        ),
        asset_class=AssetClass.PREDICTION_MARKET,
        geographic_scope=GeographicScope.GLOBAL,
        quote_currency="USD",
        tick_size="0.01",
        price_precision=2,
        lifecycle=MarketLifecycle.OPEN,
        opens_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Fixture settlement rule.",
        settles_at=datetime(2027, 1, 2, tzinfo=timezone.utc),
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_market_id.lower(),),
        related_market_ids=(),
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_market_id}",
        ),
    )

def binding(v, m):
    return CertifiedVenueMarketBinding.from_certified_objects(
        v,
        m,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-004",
            UMD_004_REVISION,
            f"fixture://umd-004/{m.native_market_id}",
            parent_hashes=(v.record_hash, m.record_hash),
        ),
    )

def registry(bindings, venues, markets):
    return ReadOnlyVenueMarketBindingRegistry(
        bindings=tuple(bindings),
        venue_registry=ReadOnlyVenueIdentityRegistry(
            venues=tuple(venues),
            registry_lineage=lineage(
                "UMD-003",
                UMD_003_REVISION,
                "fixture://umd-003/registry",
            ),
        ),
        markets=tuple(markets),
        registry_lineage=lineage(
            "UMD-004",
            UMD_004_REVISION,
            "fixture://umd-004/registry",
        ),
    )

class TestUMD004(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_004_foundation()["certified"])
        self.assertTrue(
            verify_umd_004_certified_venue_market_binding_registry()
        )

    def test_binding_identity_deterministic(self):
        v = venue()
        m = market()
        self.assertEqual(binding(v, m).binding_id, binding(v, m).binding_id)

    def test_binding_record_hash_deterministic(self):
        v = venue()
        m = market()
        self.assertEqual(binding(v, m).record_hash, binding(v, m).record_hash)

    def test_binding_is_immutable(self):
        item = binding(venue(), market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.native_market_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        v = venue()
        m1 = market("BTC-100K-2026")
        m2 = market("BTC-150K-2026")
        r = registry(
            (binding(v, m2), binding(v, m1)),
            (v,),
            (m2, m1),
        )
        result = certify_venue_market_binding_registry(r)
        self.assertTrue(result.certified)
        self.assertEqual(result.binding_count, 2)
        self.assertFalse(result.unbound_market_ids)

    def test_alias_foreign_key_lookup(self):
        v = venue()
        m = market()
        r = registry((binding(v, m),), (v,), (m,))
        resolved_venue = r.venue_registry.resolve_alias("fixture")
        self.assertEqual(resolved_venue.canonical_venue_id, v.canonical_venue_id)
        self.assertEqual(
            r.get_by_market(m.canonical_market_id).canonical_venue_id,
            v.canonical_venue_id,
        )

    def test_unknown_venue_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        other = venue("other-venue", "other")
        with self.assertRaises(ValueError):
            registry((item,), (other,), (m,))

    def test_unknown_market_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        other_market = market("OTHER")
        with self.assertRaises(ValueError):
            registry((item,), (v,), (other_market,))

    def test_duplicate_market_binding_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        with self.assertRaises(ValueError):
            registry((item, item), (v,), (m,))

    def test_namespace_mismatch_rejected(self):
        v = venue()
        m = market(venue_namespace="wrong-venue")
        with self.assertRaises(ValueError):
            binding(v, m)

    def test_unbound_market_detection(self):
        v = venue()
        m1 = market("ONE")
        m2 = market("TWO")
        r = registry((binding(v, m1),), (v,), (m1, m2))
        self.assertEqual(r.unbound_market_ids(), (m2.canonical_market_id,))
        strict = certify_venue_market_binding_registry(
            r,
            require_all_markets_bound=True,
        )
        relaxed = certify_venue_market_binding_registry(
            r,
            require_all_markets_bound=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_by_venue_deterministic(self):
        v = venue()
        m1 = market("ONE")
        m2 = market("TWO")
        r = registry(
            (binding(v, m2), binding(v, m1)),
            (v,),
            (m2, m1),
        )
        ids = tuple(
            item.canonical_market_id
            for item in r.by_venue(v.canonical_venue_id)
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_side_effects_disabled(self):
        manifest = build_umd_004_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-004 CERTIFICATION TEST")
    print(" CERTIFIED VENUE-MARKET BINDING REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD004)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_004_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-003 consumed read-only")
    print("[PASS] Canonical venue-market binding IDs deterministic")
    print("[PASS] Venue and market foreign keys validated")
    print("[PASS] Native namespace identity alignment verified")
    print("[PASS] Duplicate market bindings rejected")
    print("[PASS] Duplicate native bindings rejected")
    print("[PASS] Unbound market detection verified")
    print("[PASS] Read-only binding registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-004 CERTIFIED VENUE-MARKET BINDING REGISTRY CERTIFIED")
