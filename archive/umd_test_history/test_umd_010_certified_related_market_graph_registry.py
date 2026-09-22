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
)
from qseries_v2.universal_market_discovery.certified_market_duplicate_resolution_registry import (
    UMD_009_REVISION,
    CertifiedMarketDuplicateResolution,
    DuplicateResolutionStatus,
    ReadOnlyMarketDuplicateResolutionRegistry,
)
from qseries_v2.universal_market_discovery.certified_related_market_graph_registry import (
    UMD_010_REVISION,
    CertifiedRelatedMarketEdge,
    ReadOnlyRelatedMarketGraphRegistry,
    RelatedMarketRelationshipType,
    build_umd_010_certification_manifest,
    certify_related_market_graph_registry,
    certify_umd_010_foundation,
    verify_umd_010_certified_related_market_graph_registry,
)

FIXED = datetime(2026, 8, 5, 16, 0, tzinfo=timezone.utc)

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

def market(native_id, venue_id):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=venue_id,
            canonical_name=venue_id.title(),
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=venue_id,
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="EVENT",
        canonical_title=f"Market {native_id}",
        canonical_description="Fixture market.",
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
        duplicate_resolution_keys=(native_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def duplicate_registry(markets):
    def category_node(category_id, parent=None):
        return CertifiedMarketCategoryNode(
            category_id=category_id,
            canonical_name=category_id.title(),
            parent_category_id=parent,
            aliases=(),
            description=f"Category {category_id}.",
            metadata={},
            lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                f"fixture://umd-005/{category_id}",
            ),
        )

    category_registry = ReadOnlyMarketCategoryHierarchyRegistry(
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
    classifications = tuple(
        CertifiedMarketClassification.from_market(
            item,
            metadata={},
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
        category_registry=category_registry,
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )
    metadata_records = tuple(
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
            attributes={},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                f"fixture://umd-007/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    metadata_registry = ReadOnlyMarketMetadataRegistry(
        metadata_records=metadata_records,
        markets=tuple(markets),
        classification_registry=classification_registry,
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )
    lifecycle_records = tuple(
        CertifiedMarketLifecycleSettlementRecord.from_market(
            item,
            final_value=None,
            metadata={},
            lineage=lineage(
                "UMD-008",
                UMD_008_REVISION,
                f"fixture://umd-008/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    lifecycle_registry = ReadOnlyMarketLifecycleSettlementRegistry(
        records=lifecycle_records,
        markets=tuple(markets),
        metadata_registry=metadata_registry,
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )
    return ReadOnlyMarketDuplicateResolutionRegistry(
        resolutions=(),
        markets=tuple(markets),
        lifecycle_registry=lifecycle_registry,
        registry_lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/registry",
        ),
    )

def edge(source, target, relationship, cross_venue):
    return CertifiedRelatedMarketEdge(
        source_market_id=source.canonical_market_id,
        target_market_id=target.canonical_market_id,
        relationship_type=relationship,
        rationale_code="fixture-link",
        cross_venue=cross_venue,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-010",
            UMD_010_REVISION,
            "fixture://umd-010/edge",
        ),
    )

def registry(edges, markets):
    return ReadOnlyRelatedMarketGraphRegistry(
        edges=tuple(edges),
        markets=tuple(markets),
        duplicate_registry=duplicate_registry(markets),
        registry_lineage=lineage(
            "UMD-010",
            UMD_010_REVISION,
            "fixture://umd-010/registry",
        ),
    )

class TestUMD010(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_010_foundation()["certified"])
        self.assertTrue(
            verify_umd_010_certified_related_market_graph_registry()
        )

    def test_edge_identity_deterministic(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        self.assertEqual(
            edge(a, b, RelatedMarketRelationshipType.CORRELATED, True).edge_id,
            edge(b, a, RelatedMarketRelationshipType.CORRELATED, True).edge_id,
        )

    def test_directed_edge_identity_preserves_direction(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        self.assertNotEqual(
            edge(a, b, RelatedMarketRelationshipType.DEPENDS_ON, True).edge_id,
            edge(b, a, RelatedMarketRelationshipType.DEPENDS_ON, True).edge_id,
        )

    def test_immutable(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = edge(a, b, RelatedMarketRelationshipType.CORRELATED, True)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.cross_venue = False
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = registry(
            (edge(a, b, RelatedMarketRelationshipType.CORRELATED, True),),
            (a, b),
        )
        result = certify_related_market_graph_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["edge_count"], 1)

    def test_duplicate_edge_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        value = edge(a, b, RelatedMarketRelationshipType.CORRELATED, True)
        with self.assertRaises(ValueError):
            registry((value, value), (a, b))

    def test_unknown_market_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        with self.assertRaises(ValueError):
            registry(
                (edge(a, b, RelatedMarketRelationshipType.CORRELATED, True),),
                (a, c),
            )

    def test_cross_venue_flag_validated(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        with self.assertRaises(ValueError):
            registry(
                (edge(a, b, RelatedMarketRelationshipType.CORRELATED, False),),
                (a, b),
            )

    def test_cycle_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        with self.assertRaises(ValueError):
            registry(
                (
                    edge(a, b, RelatedMarketRelationshipType.DEPENDS_ON, True),
                    edge(b, c, RelatedMarketRelationshipType.DEPENDS_ON, True),
                    edge(c, a, RelatedMarketRelationshipType.DEPENDS_ON, True),
                ),
                (a, b, c),
            )

    def test_neighbors_deterministic(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        item = registry(
            (
                edge(a, c, RelatedMarketRelationshipType.CORRELATED, True),
                edge(a, b, RelatedMarketRelationshipType.HEDGE, True),
            ),
            (c, b, a),
        )
        self.assertEqual(
            item.neighbors(a.canonical_market_id),
            tuple(sorted((b.canonical_market_id, c.canonical_market_id))),
        )

    def test_relationship_filter(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = registry(
            (
                edge(a, b, RelatedMarketRelationshipType.HEDGE, True),
            ),
            (a, b),
        )
        self.assertEqual(
            len(item.by_relationship_type(RelatedMarketRelationshipType.HEDGE)),
            1,
        )

    def test_side_effects_disabled(self):
        manifest = build_umd_010_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-010 CERTIFICATION TEST")
    print(" CERTIFIED RELATED MARKET GRAPH REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD010)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_010_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-009 consumed read-only")
    print("[PASS] Canonical related-market edge IDs deterministic")
    print("[PASS] Directed and undirected edge identity verified")
    print("[PASS] Unknown markets rejected")
    print("[PASS] Duplicate edges rejected")
    print("[PASS] Cross-venue flags validated")
    print("[PASS] Directed relationship cycles rejected")
    print("[PASS] Neighbor traversal deterministic")
    print("[PASS] Read-only graph registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic inference and graph mutation disabled")
    print("[PASS] Persistence and publication disabled")
    print("[PASS] Q Series execution disabled")
    print("[DONE] UMD-010 CERTIFIED RELATED MARKET GRAPH REGISTRY CERTIFIED")
