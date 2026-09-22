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
from qseries_v2.universal_market_discovery.certified_market_category_hierarchy_registry import (
    UMD_005_REVISION,
    CertifiedMarketCategoryNode,
    ReadOnlyMarketCategoryHierarchyRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_classification_registry import (
    UMD_006_REVISION,
    CertifiedMarketClassification,
    ReadOnlyMarketClassificationRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_metadata_registry import (
    UMD_007_REVISION,
    CertifiedMarketMetadata,
    ReadOnlyMarketMetadataRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_lifecycle_and_settlement_registry import (
    UMD_008_REVISION,
    CertifiedMarketLifecycleSettlementRecord,
    ReadOnlyMarketLifecycleSettlementRegistry,
    build_umd_008_certification_manifest,
    certify_market_lifecycle_and_settlement_registry,
    certify_umd_008_foundation,
    verify_umd_008_certified_market_lifecycle_and_settlement_registry,
)

FIXED = datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)

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

def category_registry():
    def node(category_id, parent=None):
        return CertifiedMarketCategoryNode(
            category_id=category_id,
            canonical_name=category_id.title(),
            parent_category_id=parent,
            aliases=(),
            description=f"Category {category_id}.",
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                f"fixture://umd-005/{category_id}",
            ),
        )
    return ReadOnlyMarketCategoryHierarchyRegistry(
        categories=(
            node("markets"),
            node("crypto", "markets"),
            node("bitcoin", "crypto"),
        ),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )

def market(native_id="BTC-100K", lifecycle=MarketLifecycle.OPEN):
    settles_at = (
        datetime(2027, 1, 2, tzinfo=timezone.utc)
        if lifecycle == MarketLifecycle.SETTLED
        else None
    )
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="BTC",
        canonical_title=f"Fixture market {native_id}",
        canonical_description="Fixture market description.",
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
        lifecycle=lifecycle,
        opens_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Fixture settlement rule.",
        settles_at=settles_at,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def metadata_registry(markets):
    classifications = tuple(
        CertifiedMarketClassification.from_market(
            item,
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-006",
                UMD_006_REVISION,
                f"fixture://umd-006/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    classification_registry = ReadOnlyMarketClassificationRegistry(
        classifications=classifications,
        markets=tuple(markets),
        category_registry=category_registry(),
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )
    records = tuple(
        CertifiedMarketMetadata.from_market(
            item,
            short_title=item.native_market_id,
            symbol="BTC",
            language="en",
            timezone_name="America/Chicago",
            tags=("bitcoin",),
            keywords=("Bitcoin",),
            external_reference_ids={"fixture": item.native_market_id},
            metadata_version="1.0.0",
            attributes={"read_only": True},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                f"fixture://umd-007/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    return ReadOnlyMarketMetadataRegistry(
        metadata_records=records,
        markets=tuple(markets),
        classification_registry=classification_registry,
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )

def record(item, final_value=None, parent_hashes=()):
    return CertifiedMarketLifecycleSettlementRecord.from_market(
        item,
        final_value=final_value,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            f"fixture://umd-008/{item.native_market_id}",
            parent_hashes=parent_hashes,
        ),
    )

def registry(records, markets):
    return ReadOnlyMarketLifecycleSettlementRegistry(
        records=tuple(records),
        markets=tuple(markets),
        metadata_registry=metadata_registry(markets),
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )

class TestUMD008(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_008_foundation()["certified"])
        self.assertTrue(
            verify_umd_008_certified_market_lifecycle_and_settlement_registry()
        )

    def test_identity_deterministic(self):
        item = market()
        self.assertEqual(
            record(item).lifecycle_record_id,
            record(item).lifecycle_record_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(record(item).record_hash, record(item).record_hash)

    def test_immutable(self):
        item = record(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.lifecycle = MarketLifecycle.CLOSED
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(second), record(first)), (second, first))
        result = certify_market_lifecycle_and_settlement_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["record_count"], 2)

    def test_duplicate_market_record_rejected(self):
        item = market()
        value = record(item)
        with self.assertRaises(ValueError):
            registry((value, value), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((record(first),), (second,))

    def test_settled_requires_final_value(self):
        item = market("SETTLED", MarketLifecycle.SETTLED)
        with self.assertRaises(ValueError):
            record(item)

    def test_non_settled_rejects_final_value(self):
        with self.assertRaises(ValueError):
            record(market(), final_value="YES")

    def test_valid_transition(self):
        current_market = market("TRANSITION", MarketLifecycle.OPEN)
        next_market = market("TRANSITION", MarketLifecycle.CLOSED)
        current = record(current_market)
        nxt = record(next_market, parent_hashes=(current.record_hash,))
        self.assertTrue(current.validate_transition_to(nxt))

    def test_invalid_transition_rejected(self):
        current_market = market("TRANSITION", MarketLifecycle.OPEN)
        next_market = market("TRANSITION", MarketLifecycle.SETTLED)
        current = record(current_market)
        nxt = record(
            next_market,
            final_value="YES",
            parent_hashes=(current.record_hash,),
        )
        with self.assertRaises(ValueError):
            current.validate_transition_to(nxt)

    def test_expiration_query_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(second), record(first)), (second, first))
        results = item.markets_expiring_by(
            datetime(2027, 1, 1, tzinfo=timezone.utc)
        )
        ids = tuple(value.canonical_market_id for value in results)
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_missing_lifecycle_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(first),), (first, second))
        strict = certify_market_lifecycle_and_settlement_registry(
            item,
            require_all_markets_tracked=True,
        )
        relaxed = certify_market_lifecycle_and_settlement_registry(
            item,
            require_all_markets_tracked=False,
        )
        self.assertFalse(strict["certified"])
        self.assertTrue(relaxed["certified"])

    def test_side_effects_disabled(self):
        manifest = build_umd_008_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-008 CERTIFICATION TEST")
    print(" CERTIFIED MARKET LIFECYCLE AND SETTLEMENT REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD008)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_008_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-007 consumed read-only")
    print("[PASS] Canonical lifecycle record IDs deterministic")
    print("[PASS] Market and metadata foreign keys validated")
    print("[PASS] Expiration and settlement timestamps validated")
    print("[PASS] Settled final-value requirements enforced")
    print("[PASS] Lifecycle transition rules certified")
    print("[PASS] Invalid lifecycle transitions rejected")
    print("[PASS] Expiration lookup deterministic")
    print("[PASS] Missing lifecycle tracking detected")
    print("[PASS] Read-only lifecycle registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic advancement and settlement disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-008 CERTIFIED MARKET LIFECYCLE AND SETTLEMENT REGISTRY CERTIFIED")
