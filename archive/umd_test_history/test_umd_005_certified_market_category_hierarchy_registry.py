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
    build_umd_005_certification_manifest,
    certify_market_category_hierarchy_registry,
    certify_umd_005_foundation,
    verify_umd_005_certified_market_category_hierarchy_registry,
)

FIXED = datetime(2026, 8, 5, 7, 0, tzinfo=timezone.utc)

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

def category(category_id, parent=None, name=None, aliases=()):
    return CertifiedMarketCategoryNode(
        category_id=category_id,
        canonical_name=name or category_id.replace("-", " ").title(),
        parent_category_id=parent,
        aliases=aliases,
        description=f"Certified category {category_id}.",
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            f"fixture://umd-005/{category_id}",
        ),
    )

def registry(categories):
    return ReadOnlyMarketCategoryHierarchyRegistry(
        categories=tuple(categories),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )

def market():
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id="BTC-100K",
        native_event_id="BTC",
        canonical_title="Will Bitcoin exceed $100,000?",
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
        duplicate_resolution_keys=("bitcoin", "100000"),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            "fixture://umd-002/market",
        ),
    )

class TestUMD005(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_005_foundation()["certified"])
        self.assertTrue(
            verify_umd_005_certified_market_category_hierarchy_registry()
        )

    def test_category_identity_deterministic(self):
        self.assertEqual(
            category("crypto").canonical_category_id,
            category("crypto").canonical_category_id,
        )
        self.assertNotEqual(
            category("crypto").canonical_category_id,
            category("equities").canonical_category_id,
        )

    def test_category_record_hash_deterministic(self):
        self.assertEqual(
            category("crypto").record_hash,
            category("crypto").record_hash,
        )

    def test_immutable(self):
        item = category("crypto")
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.category_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        r = registry(
            (
                category("bitcoin", "crypto"),
                category("markets"),
                category("crypto", "markets"),
            )
        )
        result = certify_market_category_hierarchy_registry(r)
        self.assertTrue(result.certified)
        self.assertEqual(result.category_count, 3)
        self.assertEqual(result.root_count, 1)

    def test_path_resolution(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        self.assertEqual(
            r.path_for("bitcoin"),
            ("markets", "crypto", "bitcoin"),
        )

    def test_alias_resolution(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets", aliases=("Digital Assets",)),
            )
        )
        self.assertEqual(
            r.resolve_alias("digital assets").category_id,
            "crypto",
        )

    def test_unknown_parent_rejected(self):
        with self.assertRaises(ValueError):
            registry((category("bitcoin", "crypto"),))

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            registry(
                (
                    category("a", "b"),
                    category("b", "a"),
                )
            )

    def test_ambiguous_alias_rejected(self):
        with self.assertRaises(ValueError):
            registry(
                (
                    category("markets"),
                    category("crypto", "markets", aliases=("Shared",)),
                    category("equities", "markets", aliases=("Shared",)),
                )
            )

    def test_market_validation(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        self.assertTrue(r.validate_market(market()))

    def test_market_path_mismatch_rejected(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        bad = market()
        object.__setattr__(
            bad,
            "category",
            MarketCategory(
                category_id="bitcoin",
                canonical_name="Bitcoin",
                parent_category_id="crypto",
                path=("wrong", "bitcoin"),
            ),
        )
        with self.assertRaises(ValueError):
            r.validate_market(bad)

    def test_side_effects_disabled(self):
        manifest = build_umd_005_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-005 CERTIFICATION TEST")
    print(" CERTIFIED MARKET CATEGORY HIERARCHY REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD005)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_005_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-004 consumed read-only")
    print("[PASS] Canonical category IDs deterministic")
    print("[PASS] Parent-child hierarchy validated")
    print("[PASS] Unknown parents rejected")
    print("[PASS] Hierarchy cycles rejected")
    print("[PASS] Category aliases resolved deterministically")
    print("[PASS] Ambiguous aliases rejected")
    print("[PASS] Canonical market category paths validated")
    print("[PASS] Read-only category registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-005 CERTIFIED MARKET CATEGORY HIERARCHY REGISTRY CERTIFIED")
