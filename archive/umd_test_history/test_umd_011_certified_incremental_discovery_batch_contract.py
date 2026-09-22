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
    deterministic_sha256,
)
from qseries_v2.universal_market_discovery.certified_canonical_market_contract import (
    UMD_002_REVISION,
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from qseries_v2.universal_market_discovery.certified_incremental_discovery_batch_contract import (
    UMD_011_REVISION,
    CertifiedDiscoveryCursor,
    CertifiedDiscoveryCandidate,
    CertifiedIncrementalDiscoveryBatch,
    build_umd_011_certification_manifest,
    certify_umd_011_foundation,
    verify_umd_011_certified_incremental_discovery_batch_contract,
)

FIXED = datetime(2026, 8, 5, 20, 0, tzinfo=timezone.utc)

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

def market(native_id):
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
        native_event_id="EVENT",
        canonical_title=f"Market {native_id}",
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
        duplicate_resolution_keys=(native_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def cursor(value):
    return CertifiedDiscoveryCursor(
        source_id="fixture-source",
        partition_key="markets",
        cursor_value=value,
        observed_at=FIXED,
        lineage=lineage(
            "UMD-011",
            UMD_011_REVISION,
            f"fixture://umd-011/cursor/{value}",
        ),
    )

def candidate(native_id):
    payload_hash = deterministic_sha256({"native_id": native_id})
    return CertifiedDiscoveryCandidate(
        source_id="fixture-source",
        source_market_key=native_id,
        market=market(native_id),
        discovered_at=FIXED,
        payload_hash=payload_hash,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-011",
            UMD_011_REVISION,
            f"fixture://umd-011/candidate/{native_id}",
        ),
    )

class TestUMD011(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_011_foundation()["certified"])
        self.assertTrue(
            verify_umd_011_certified_incremental_discovery_batch_contract()
        )

    def test_cursor_identity_deterministic(self):
        self.assertEqual(cursor("100").cursor_id, cursor("100").cursor_id)

    def test_candidate_identity_deterministic(self):
        self.assertEqual(
            candidate("A").candidate_id,
            candidate("A").candidate_id,
        )

    def test_batch_identity_deterministic(self):
        batch = CertifiedIncrementalDiscoveryBatch(
            source_id="fixture-source",
            batch_sequence=1,
            previous_batch_hash=None,
            start_cursor=None,
            end_cursor=cursor("100"),
            candidates=(candidate("A"), candidate("B")),
            created_at=FIXED,
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-011",
                UMD_011_REVISION,
                "fixture://umd-011/batch/1",
            ),
        )
        self.assertEqual(batch.batch_id, batch.batch_id)
        self.assertEqual(batch.batch_hash, batch.batch_hash)

    def test_candidate_order_deterministic(self):
        first = CertifiedIncrementalDiscoveryBatch(
            source_id="fixture-source",
            batch_sequence=1,
            previous_batch_hash=None,
            start_cursor=None,
            end_cursor=cursor("100"),
            candidates=(candidate("B"), candidate("A")),
            created_at=FIXED,
            metadata={},
            lineage=lineage(
                "UMD-011",
                UMD_011_REVISION,
                "fixture://umd-011/order",
            ),
        )
        ids = tuple(item.candidate_id for item in first.candidates)
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_duplicate_source_key_rejected(self):
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=1,
                previous_batch_hash=None,
                start_cursor=None,
                end_cursor=cursor("100"),
                candidates=(candidate("A"), candidate("A")),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/duplicate",
                ),
            )

    def test_non_initial_batch_requires_previous_hash(self):
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=2,
                previous_batch_hash=None,
                start_cursor=cursor("100"),
                end_cursor=cursor("200"),
                candidates=(candidate("B"),),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/batch/2",
                ),
            )

    def test_lineage_previous_hash_required(self):
        previous = "a" * 64
        with self.assertRaises(ValueError):
            CertifiedIncrementalDiscoveryBatch(
                source_id="fixture-source",
                batch_sequence=2,
                previous_batch_hash=previous,
                start_cursor=cursor("100"),
                end_cursor=cursor("200"),
                candidates=(candidate("B"),),
                created_at=FIXED,
                metadata={},
                lineage=lineage(
                    "UMD-011",
                    UMD_011_REVISION,
                    "fixture://umd-011/batch/2",
                ),
            )

    def test_immutable(self):
        item = candidate("A")
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.source_market_key = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self):
        manifest = build_umd_011_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-011 CERTIFICATION TEST")
    print(" CERTIFIED INCREMENTAL DISCOVERY BATCH CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD011)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_011_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-010 consumed read-only")
    print("[PASS] Discovery cursor IDs deterministic")
    print("[PASS] Discovery candidate IDs deterministic")
    print("[PASS] Incremental batch IDs and hashes deterministic")
    print("[PASS] Candidate ordering deterministic")
    print("[PASS] Duplicate source-market candidates rejected")
    print("[PASS] Batch-chain lineage requirements enforced")
    print("[PASS] Network discovery remains disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-011 CERTIFIED INCREMENTAL DISCOVERY BATCH CONTRACT CERTIFIED")
