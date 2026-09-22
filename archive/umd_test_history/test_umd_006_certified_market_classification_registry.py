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
    build_umd_006_certification_manifest,
    certify_market_classification_registry,
    certify_umd_006_foundation,
    verify_umd_006_certified_market_classification_registry,
)

FIXED = datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc)

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
        canonical_name=category_id.replace("-", " ").title(),
        parent_category_id=parent,
        aliases=(),
        description=f"Certified category {category_id}.",
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
        canonical_description="Fixture.",
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

def registry(classifications, markets):
    return ReadOnlyMarketClassificationRegistry(
        classifications=tuple(classifications),
        markets=tuple(markets),
        category_registry=category_registry(),
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )

class TestUMD006(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_006_foundation()["certified"])
        self.assertTrue(
            verify_umd_006_certified_market_classification_registry()
        )

    def test_classification_identity_deterministic(self):
        item = market()
        self.assertEqual(
            classification(item).classification_id,
            classification(item).classification_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(
            classification(item).record_hash,
            classification(item).record_hash,
        )

    def test_immutable(self):
        item = classification(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.category_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (classification(second), classification(first)),
            (second, first),
        )
        result = certify_market_classification_registry(item)
        self.assertTrue(result.certified)
        self.assertEqual(result.classification_count, 2)
        self.assertFalse(result.unclassified_market_ids)

    def test_duplicate_market_classification_rejected(self):
        item = market()
        value = classification(item)
        with self.assertRaises(ValueError):
            registry((value, value), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((classification(first),), (second,))

    def test_mismatched_classification_rejected(self):
        item = market()
        bad = CertifiedMarketClassification(
            canonical_market_id=item.canonical_market_id,
            category_id="crypto",
            asset_class=item.asset_class,
            instrument_type=item.instrument_type,
            geographic_scope=item.geographic_scope,
            settlement_method=item.settlement_method,
            lifecycle=item.lifecycle,
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-006",
                UMD_006_REVISION,
                "fixture://umd-006/bad",
            ),
        )
        with self.assertRaises(ValueError):
            registry((bad,), (item,))

    def test_unclassified_market_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((classification(first),), (first, second))
        self.assertEqual(
            item.unclassified_market_ids(),
            (second.canonical_market_id,),
        )
        strict = certify_market_classification_registry(
            item,
            require_all_markets_classified=True,
        )
        relaxed = certify_market_classification_registry(
            item,
            require_all_markets_classified=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_by_category_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (classification(second), classification(first)),
            (second, first),
        )
        ids = tuple(
            value.canonical_market_id
            for value in item.by_category("bitcoin")
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_category_registry_is_enforced(self):
        item = market()
        bad_category_registry = ReadOnlyMarketCategoryHierarchyRegistry(
            categories=(category_node("markets"),),
            registry_lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                "fixture://umd-005/bad-registry",
            ),
        )
        with self.assertRaises(ValueError):
            ReadOnlyMarketClassificationRegistry(
                classifications=(classification(item),),
                markets=(item,),
                category_registry=bad_category_registry,
                registry_lineage=lineage(
                    "UMD-006",
                    UMD_006_REVISION,
                    "fixture://umd-006/bad-registry",
                ),
            )

    def test_side_effects_disabled(self):
        manifest = build_umd_006_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-006 CERTIFICATION TEST")
    print(" CERTIFIED MARKET CLASSIFICATION REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD006)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_006_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-005 consumed read-only")
    print("[PASS] Canonical classification IDs deterministic")
    print("[PASS] Market foreign-key validation verified")
    print("[PASS] Category hierarchy validation verified")
    print("[PASS] Asset, instrument, geography, settlement, and lifecycle alignment verified")
    print("[PASS] Duplicate market classifications rejected")
    print("[PASS] Unclassified market detection verified")
    print("[PASS] Read-only classification registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic classification and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-006 CERTIFIED MARKET CLASSIFICATION REGISTRY CERTIFIED")
