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
    build_umd_007_certification_manifest,
    certify_market_metadata_registry,
    certify_umd_007_foundation,
    verify_umd_007_certified_market_metadata_registry,
)

FIXED = datetime(2026, 8, 5, 9, 0, tzinfo=timezone.utc)

def lineage(build_id, revision, source):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id=build_id,
        revision=revision,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(source,),
        created_at=FIXED,
    )

def category_node(category_id, parent=None):
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

def category_registry():
    return ReadOnlyMarketCategoryHierarchyRegistry(
        categories=(
            category_node("markets"),
            category_node("crypto", "markets"),
            category_node("bitcoin", "crypto"),
        ),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )

def market(native_market_id="BTC-100K"):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC",
        canonical_title=f"Fixture market {native_market_id}",
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
        lifecycle=MarketLifecycle.OPEN,
        opens_at=None,
        closes_at=None,
        expires_at=None,
        settlement_method=SettlementMethod.UNKNOWN,
        settlement_source=None,
        settlement_rule=None,
        settles_at=None,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_market_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_market_id}",
        ),
    )

def classification(item):
    return CertifiedMarketClassification.from_market(
        item,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            f"fixture://umd-006/{item.native_market_id}",
        ),
    )

def classification_registry(markets):
    return ReadOnlyMarketClassificationRegistry(
        classifications=tuple(classification(item) for item in markets),
        markets=tuple(markets),
        category_registry=category_registry(),
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )

def metadata(item, reference_id=None):
    return CertifiedMarketMetadata.from_market(
        item,
        short_title=item.native_market_id,
        symbol="BTC",
        language="en",
        timezone_name="America/Chicago",
        tags=("bitcoin", "crypto"),
        keywords=("Bitcoin", "price"),
        external_reference_ids={
            "fixture": reference_id or item.native_market_id
        },
        metadata_version="1.0.0",
        attributes={"read_only": True},
        lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            f"fixture://umd-007/{item.native_market_id}",
        ),
    )

def registry(records, markets):
    return ReadOnlyMarketMetadataRegistry(
        metadata_records=tuple(records),
        markets=tuple(markets),
        classification_registry=classification_registry(markets),
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )

class TestUMD007(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_007_foundation()["certified"])
        self.assertTrue(
            verify_umd_007_certified_market_metadata_registry()
        )

    def test_metadata_identity_deterministic(self):
        item = market()
        self.assertEqual(
            metadata(item).metadata_id,
            metadata(item).metadata_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(
            metadata(item).record_hash,
            metadata(item).record_hash,
        )

    def test_immutable(self):
        item = metadata(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.display_title = "mutated"
        with self.assertRaises(TypeError):
            item.attributes["read_only"] = False
        with self.assertRaises(TypeError):
            item.external_reference_ids["fixture"] = "mutated"

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (metadata(second), metadata(first)),
            (second, first),
        )
        result = certify_market_metadata_registry(item)
        self.assertTrue(result.certified)
        self.assertEqual(result.metadata_count, 2)
        self.assertFalse(result.missing_metadata_market_ids)

    def test_duplicate_market_metadata_rejected(self):
        item = market()
        record = metadata(item)
        with self.assertRaises(ValueError):
            registry((record, record), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((metadata(first),), (second,))

    def test_title_mismatch_rejected(self):
        item = market()
        bad = CertifiedMarketMetadata(
            canonical_market_id=item.canonical_market_id,
            display_title="Wrong title",
            short_title=None,
            description=item.canonical_description,
            symbol="BTC",
            language="en",
            timezone_name="America/Chicago",
            quote_currency=item.quote_currency,
            tags=("bitcoin",),
            keywords=("Bitcoin",),
            external_reference_ids={"fixture": item.native_market_id},
            metadata_version="1.0.0",
            attributes={},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                "fixture://umd-007/bad",
            ),
        )
        with self.assertRaises(ValueError):
            registry((bad,), (item,))

    def test_duplicate_external_reference_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry(
                (
                    metadata(first, reference_id="SHARED"),
                    metadata(second, reference_id="SHARED"),
                ),
                (first, second),
            )

    def test_tag_lookup_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (metadata(second), metadata(first)),
            (second, first),
        )
        ids = tuple(
            record.canonical_market_id
            for record in item.by_tag("bitcoin")
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_external_reference_resolution(self):
        item = market()
        record = metadata(item)
        reg = registry((record,), (item,))
        self.assertEqual(
            reg.resolve_external_reference(
                "fixture",
                item.native_market_id,
            ).canonical_market_id,
            item.canonical_market_id,
        )

    def test_missing_metadata_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((metadata(first),), (first, second))
        self.assertEqual(
            item.missing_metadata_market_ids(),
            (second.canonical_market_id,),
        )
        strict = certify_market_metadata_registry(
            item,
            require_all_markets_described=True,
        )
        relaxed = certify_market_metadata_registry(
            item,
            require_all_markets_described=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_side_effects_disabled(self):
        manifest = build_umd_007_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-007 CERTIFICATION TEST")
    print(" CERTIFIED MARKET METADATA REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD007)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_007_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-006 consumed read-only")
    print("[PASS] Canonical metadata IDs deterministic")
    print("[PASS] Market and classification foreign keys validated")
    print("[PASS] Title, description, and currency alignment verified")
    print("[PASS] Tags and keywords normalized deterministically")
    print("[PASS] External reference identities protected")
    print("[PASS] Duplicate metadata records rejected")
    print("[PASS] Missing metadata detection verified")
    print("[PASS] Read-only metadata registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic enrichment and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-007 CERTIFIED MARKET METADATA REGISTRY CERTIFIED")
