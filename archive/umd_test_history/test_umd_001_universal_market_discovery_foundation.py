from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    UMD_BUILD_ID,
    UMD_REVISION,
    PRIMARY_MISSION,
    PERMANENT_ARCHITECTURE,
    CanonicalMarketIdentity,
    ExpirationMetadata,
    ImmutableLineage,
    MarketCategory,
    MarketInstrumentType,
    MarketLifecycle,
    ReadOnlyMarketRegistry,
    SettlementMetadata,
    SettlementMethod,
    VenueIdentity,
    build_umd_foundation_manifest,
    canonical_json,
    certify_umd_foundation,
    deterministic_sha256,
    verify_umd_foundation,
)


FIXED_TIME = datetime(2026, 8, 4, 20, 25, tzinfo=timezone.utc)


def make_lineage(*, source_refs=("fixture://market/1",)) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-001",
        revision=UMD_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=source_refs,
        created_at=FIXED_TIME,
    )


def make_market(
    native_market_id: str = "BTC-100K-2026",
    *,
    title: str = "Will Bitcoin exceed $100,000 before 2027?",
) -> CanonicalMarketIdentity:
    venue = VenueIdentity(
        venue_id="fixture-venue",
        canonical_name="Fixture Venue",
        venue_type="prediction_market",
        jurisdiction="US",
        native_market_namespace="fixture",
        metadata={"api_version": "test"},
    )
    category = MarketCategory(
        category_id="bitcoin",
        canonical_name="Bitcoin",
        parent_category_id="crypto",
        path=("markets", "crypto", "bitcoin"),
    )
    return CanonicalMarketIdentity(
        venue=venue,
        native_market_id=native_market_id,
        canonical_title=title,
        instrument_type=MarketInstrumentType.BINARY,
        category=category,
        lifecycle=MarketLifecycle.OPEN,
        expiration=ExpirationMetadata(
            opens_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            closes_at=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
            expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        ),
        settlement=SettlementMetadata(
            method=SettlementMethod.THIRD_PARTY_SOURCE,
            settlement_source="Certified benchmark source",
            settlement_rule="Resolve YES when the certified benchmark exceeds 100000.",
            settles_at=None,
            final_value=None,
        ),
        outcome_labels=("YES", "NO"),
        market_metadata={"currency": "USD", "read_only": True},
        lineage=make_lineage(),
    )


class TestUMD001Foundation(unittest.TestCase):
    def test_manifest_certifies(self) -> None:
        manifest = build_umd_foundation_manifest()
        certification = certify_umd_foundation(manifest)
        self.assertTrue(certification["certified"])
        self.assertTrue(verify_umd_foundation())
        self.assertEqual(manifest.build_id, UMD_BUILD_ID)
        self.assertEqual(manifest.primary_mission, PRIMARY_MISSION)
        self.assertEqual(manifest.permanent_architecture, PERMANENT_ARCHITECTURE)
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_deterministic_canonical_json(self) -> None:
        left = {"b": 2, "a": 1, "nested": {"z": 3, "y": 2}}
        right = {"nested": {"y": 2, "z": 3}, "a": 1, "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(
            deterministic_sha256(left),
            deterministic_sha256(right),
        )

    def test_canonical_market_id_is_deterministic_and_identity_bound(self) -> None:
        first = make_market()
        second = make_market()
        changed_title = make_market(title="Different display title")
        changed_native_id = make_market(native_market_id="BTC-150K-2026")

        self.assertEqual(first.canonical_market_id, second.canonical_market_id)
        self.assertEqual(first.canonical_market_id, changed_title.canonical_market_id)
        self.assertNotEqual(
            first.canonical_market_id,
            changed_native_id.canonical_market_id,
        )
        self.assertTrue(first.canonical_market_id.startswith("umd:mkt:"))

    def test_market_record_hash_is_deterministic(self) -> None:
        first = make_market()
        second = make_market()
        self.assertEqual(first.record_hash, second.record_hash)
        self.assertEqual(len(first.record_hash), 64)

    def test_immutable_contracts(self) -> None:
        market = make_market()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            market.canonical_title = "mutated"
        with self.assertRaises(TypeError):
            market.market_metadata["currency"] = "EUR"
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            market.lineage.revision = "MUTATED"

    def test_registry_is_order_independent_and_read_only(self) -> None:
        market_a = make_market(native_market_id="A")
        market_b = make_market(native_market_id="B")
        lineage = make_lineage(source_refs=("fixture://registry",))

        first = ReadOnlyMarketRegistry(
            markets=(market_b, market_a),
            registry_lineage=lineage,
        )
        second = ReadOnlyMarketRegistry(
            markets=(market_a, market_b),
            registry_lineage=lineage,
        )

        self.assertEqual(first.registry_hash, second.registry_hash)
        self.assertEqual(
            [item.canonical_market_id for item in first.markets],
            sorted(item.canonical_market_id for item in first.markets),
        )
        self.assertIsNotNone(first.get(market_a.canonical_market_id))
        self.assertEqual(len(first.by_venue("fixture-venue")), 2)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            first.markets = ()

    def test_duplicate_registry_identity_rejected(self) -> None:
        market = make_market()
        with self.assertRaises(ValueError):
            ReadOnlyMarketRegistry(
                markets=(market, market),
                registry_lineage=make_lineage(
                    source_refs=("fixture://registry",)
                ),
            )

    def test_expiration_order_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            ExpirationMetadata(
                opens_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
                closes_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )

    def test_lineage_hash_is_deterministic(self) -> None:
        first = make_lineage(source_refs=("b", "a", "a"))
        second = make_lineage(source_refs=("a", "b"))
        self.assertEqual(first.lineage_hash, second.lineage_hash)

    def test_no_runtime_side_effect_surfaces(self) -> None:
        manifest = build_umd_foundation_manifest()
        serialized = json.loads(canonical_json(manifest))
        self.assertEqual(serialized["registry_mode"], "read_only")
        for field_name in (
            "network_enabled",
            "persistence_enabled",
            "mutation_enabled",
            "publication_enabled",
            "execution_enabled",
        ):
            self.assertFalse(serialized[field_name])


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-001 CERTIFICATION TEST")
    print(" UNIVERSAL MARKET DISCOVERY FOUNDATION")
    print("=" * 64)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD001Foundation
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_foundation_manifest()
    certification = certify_umd_foundation(manifest)
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] Canonical market identity contract deterministic")
    print("[PASS] Venue abstraction contract immutable")
    print("[PASS] Category, expiration, and settlement contracts verified")
    print("[PASS] Registry ordering and replay deterministic")
    print("[PASS] Immutable lineage verified")
    print("[PASS] OIT and OML remain frozen and read-only")
    print("[PASS] Network discovery disabled")
    print("[PASS] Persistence and mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-001 UNIVERSAL MARKET DISCOVERY FOUNDATION CERTIFIED")
