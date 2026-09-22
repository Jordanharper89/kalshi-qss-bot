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
    build_umd_002_certification_manifest,
    certify_canonical_market,
    certify_umd_002_foundation,
    verify_umd_002_certified_canonical_market_contract,
)

FIXED = datetime(2026, 8, 5, 4, 15, tzinfo=timezone.utc)

def lineage(parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-002",
        revision=UMD_002_REVISION,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=("fixture://umd-002/market/1",),
        created_at=FIXED,
    )

def market(native_market_id="BTC-100K-2026", title="Will Bitcoin exceed $100,000 before 2027?", related=(), line=None):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={"adapter": "fixture"},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC-2026",
        canonical_title=title,
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
        closes_at=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Resolve YES when benchmark exceeds 100000.",
        settles_at=datetime(2027, 1, 2, tzinfo=timezone.utc),
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=("bitcoin", "above-100000", "before-2027"),
        related_market_ids=related,
        metadata={"read_only": True},
        lineage=line or lineage(),
    )

class TestUMD002(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_002_foundation()["certified"])
        self.assertTrue(verify_umd_002_certified_canonical_market_contract())

    def test_market_certifies(self):
        self.assertTrue(certify_canonical_market(market()).certified)

    def test_identity_bound(self):
        a = market()
        b = market(title="Different title")
        c = market(native_market_id="BTC-150K-2026")
        self.assertEqual(a.canonical_market_id, b.canonical_market_id)
        self.assertNotEqual(a.canonical_market_id, c.canonical_market_id)

    def test_record_hash_deterministic(self):
        self.assertEqual(market().record_hash, market().record_hash)

    def test_duplicate_fingerprint_deterministic(self):
        self.assertEqual(market().duplicate_fingerprint, market(title="Different").duplicate_fingerprint)

    def test_immutable(self):
        item = market()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.canonical_title = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_binary_requires_two_outcomes(self):
        base = market()
        with self.assertRaises(ValueError):
            CertifiedCanonicalMarket(
                venue=base.venue,
                native_market_id="BAD",
                native_event_id=None,
                canonical_title="Bad",
                canonical_description=None,
                instrument_type=MarketInstrumentType.BINARY,
                category=base.category,
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
                outcome_labels=("YES",),
                duplicate_resolution_keys=("bad",),
                related_market_ids=(),
                metadata={},
                lineage=lineage(),
            )

    def test_timestamp_order(self):
        base = market()
        with self.assertRaises(ValueError):
            CertifiedCanonicalMarket(
                venue=base.venue,
                native_market_id="BAD-TIME",
                native_event_id=None,
                canonical_title="Bad Time",
                canonical_description=None,
                instrument_type=MarketInstrumentType.BINARY,
                category=base.category,
                asset_class=AssetClass.PREDICTION_MARKET,
                geographic_scope=GeographicScope.GLOBAL,
                quote_currency="USD",
                tick_size="0.01",
                price_precision=2,
                lifecycle=MarketLifecycle.OPEN,
                opens_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
                closes_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                expires_at=None,
                settlement_method=SettlementMethod.UNKNOWN,
                settlement_source=None,
                settlement_rule=None,
                settles_at=None,
                outcome_labels=("YES", "NO"),
                duplicate_resolution_keys=("bad-time",),
                related_market_ids=(),
                metadata={},
                lineage=lineage(),
            )

    def test_lineage_update_guard(self):
        original = market()
        with self.assertRaises(ValueError):
            original.with_related_market_ids(("umd:mkt:" + "a" * 64,), lineage=lineage())
        updated = original.with_related_market_ids(
            ("umd:mkt:" + "a" * 64,),
            lineage=lineage((original.record_hash,)),
        )
        self.assertIn(original.record_hash, updated.lineage.parent_hashes)

    def test_self_reference_rejected(self):
        original = market()
        with self.assertRaises(ValueError):
            market(related=(original.canonical_market_id,))

    def test_side_effects_disabled(self):
        manifest = build_umd_002_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-002 CERTIFICATION TEST")
    print(" CERTIFIED CANONICAL MARKET CONTRACT")
    print("=" * 64)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD002)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_002_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 consumed read-only")
    print("[PASS] Canonical Market ID deterministic")
    print("[PASS] Native venue identity binding verified")
    print("[PASS] Canonical schema immutable")
    print("[PASS] Expiration and settlement ordering verified")
    print("[PASS] Duplicate fingerprint deterministic")
    print("[PASS] Related-market lineage update guarded")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-002 CERTIFIED CANONICAL MARKET CONTRACT CERTIFIED")
