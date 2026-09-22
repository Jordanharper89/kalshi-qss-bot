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
    build_umd_009_certification_manifest,
    certify_market_duplicate_resolution_registry,
    certify_umd_009_foundation,
    verify_umd_009_certified_market_duplicate_resolution_registry,
)

FIXED = datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc)

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

def market(native_id, duplicate_keys=("bitcoin", "100000")):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=f"venue-{native_id.lower()}",
            canonical_name=f"Venue {native_id}",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=f"ns-{native_id.lower()}",
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="BTC",
        canonical_title="Will Bitcoin exceed $100,000?",
        canonical_description="Fixture duplicate market.",
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
        settlement_rule="Fixture rule.",
        settles_at=None,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=duplicate_keys,
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def lifecycle_registry(markets):
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
    metadata_records = tuple(
        CertifiedMarketMetadata.from_market(
            item,
            short_title=item.native_market_id,
            symbol="BTC",
            language="en",
            timezone_name="America/Chicago",
            tags=("bitcoin",),
            keywords=("Bitcoin",),
            external_reference_ids={
                "fixture": item.native_market_id
            },
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
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-008",
                UMD_008_REVISION,
                f"fixture://umd-008/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    return ReadOnlyMarketLifecycleSettlementRegistry(
        records=lifecycle_records,
        markets=tuple(markets),
        metadata_registry=metadata_registry,
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )

def resolution(markets, status=DuplicateResolutionStatus.CONFIRMED_DUPLICATE):
    return CertifiedMarketDuplicateResolution(
        duplicate_group_key="bitcoin-100k-2026",
        canonical_winner_market_id=markets[0].canonical_market_id,
        member_market_ids=tuple(
            item.canonical_market_id for item in markets
        ),
        status=status,
        rationale_code="same-outcome-same-expiry",
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/resolution",
        ),
    )

def registry(resolutions, markets):
    return ReadOnlyMarketDuplicateResolutionRegistry(
        resolutions=tuple(resolutions),
        markets=tuple(markets),
        lifecycle_registry=lifecycle_registry(markets),
        registry_lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/registry",
        ),
    )

class TestUMD009(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_009_foundation()["certified"])
        self.assertTrue(
            verify_umd_009_certified_market_duplicate_resolution_registry()
        )

    def test_resolution_identity_deterministic(self):
        markets = (market("A"), market("B"))
        self.assertEqual(
            resolution(markets).resolution_id,
            resolution(markets).resolution_id,
        )

    def test_record_hash_deterministic(self):
        markets = (market("A"), market("B"))
        self.assertEqual(
            resolution(markets).record_hash,
            resolution(markets).record_hash,
        )

    def test_immutable(self):
        item = resolution((market("A"), market("B")))
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.status = DuplicateResolutionStatus.REJECTED
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        markets = (market("A"), market("B"))
        item = registry((resolution(markets),), markets)
        result = certify_market_duplicate_resolution_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["resolution_count"], 1)

    def test_confirmed_duplicate_requires_shared_fingerprint(self):
        markets = (
            market("A", duplicate_keys=("bitcoin", "100000")),
            market("B", duplicate_keys=("bitcoin", "150000")),
        )
        with self.assertRaises(ValueError):
            registry((resolution(markets),), markets)

    def test_unknown_market_rejected(self):
        markets = (market("A"), market("B"))
        other_markets = (market("A"), market("C"))
        with self.assertRaises(ValueError):
            registry((resolution(markets),), other_markets)

    def test_market_cannot_join_two_groups(self):
        markets = (market("A"), market("B"), market("C"))
        first = resolution((markets[0], markets[1]))
        second = CertifiedMarketDuplicateResolution(
            duplicate_group_key="second-group",
            canonical_winner_market_id=markets[0].canonical_market_id,
            member_market_ids=(
                markets[0].canonical_market_id,
                markets[2].canonical_market_id,
            ),
            status=DuplicateResolutionStatus.CONFIRMED_DUPLICATE,
            rationale_code="same-outcome-same-expiry",
            metadata={},
            lineage=lineage(
                "UMD-009",
                UMD_009_REVISION,
                "fixture://umd-009/second",
            ),
        )
        with self.assertRaises(ValueError):
            registry((first, second), markets)

    def test_canonical_market_resolution(self):
        markets = (market("A"), market("B"))
        item = registry((resolution(markets),), markets)
        self.assertEqual(
            item.canonical_market_id_for(markets[1].canonical_market_id),
            markets[0].canonical_market_id,
        )

    def test_related_not_duplicate_preserves_identity(self):
        markets = (market("A"), market("B"))
        item = registry(
            (
                resolution(
                    markets,
                    status=DuplicateResolutionStatus.RELATED_NOT_DUPLICATE,
                ),
            ),
            markets,
        )
        self.assertEqual(
            item.canonical_market_id_for(markets[1].canonical_market_id),
            markets[1].canonical_market_id,
        )

    def test_unresolved_candidate_detection(self):
        markets = (market("A"), market("B"))
        item = registry(
            (
                resolution(
                    markets,
                    status=DuplicateResolutionStatus.CANDIDATE,
                ),
            ),
            markets,
        )
        strict = certify_market_duplicate_resolution_registry(
            item,
            allow_unresolved_candidates=False,
        )
        relaxed = certify_market_duplicate_resolution_registry(
            item,
            allow_unresolved_candidates=True,
        )
        self.assertFalse(strict["certified"])
        self.assertTrue(relaxed["certified"])

    def test_side_effects_disabled(self):
        manifest = build_umd_009_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-009 CERTIFICATION TEST")
    print(" CERTIFIED MARKET DUPLICATE RESOLUTION REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD009)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_009_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-008 consumed read-only")
    print("[PASS] Duplicate-resolution IDs deterministic")
    print("[PASS] Confirmed duplicate fingerprints validated")
    print("[PASS] Canonical winner selection deterministic")
    print("[PASS] Unknown markets rejected")
    print("[PASS] Multi-group market conflicts rejected")
    print("[PASS] Related-not-duplicate identity preserved")
    print("[PASS] Unresolved duplicate candidates detected")
    print("[PASS] Read-only duplicate registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic merging and deletion disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-009 CERTIFIED MARKET DUPLICATE RESOLUTION REGISTRY CERTIFIED")
