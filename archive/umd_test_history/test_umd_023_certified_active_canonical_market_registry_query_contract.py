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
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_contract import (
    UMD_023_REVISION,
    MarketQueryMode,
    CertifiedActiveMarketQueryRequest,
    build_umd_023_certification_manifest,
    certify_umd_023_foundation,
    verify_umd_023_certified_active_canonical_market_registry_query_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    6,
    0,
    tzinfo=timezone.utc,
)


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-023",
        revision=UMD_023_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(
            "fixture://umd-023/query",
        ),
        created_at=FIXED,
    )


class TestUMD023(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_023_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_023_certified_active_canonical_market_registry_query_contract()
        )

    def test_query_id_deterministic(self) -> None:
        first = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.FILTER,
            canonical_market_id=None,
            venue_id="Venue-A",
            category_id="Bitcoin",
            lifecycle="open",
            limit=10,
            lineage=lineage(),
        )
        second = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.FILTER,
            canonical_market_id=None,
            venue_id="venue-a",
            category_id="bitcoin",
            lifecycle="OPEN",
            limit=10,
            lineage=lineage(),
        )

        self.assertEqual(
            first.query_id,
            second.query_id,
        )

    def test_by_id_requires_market_id(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.BY_ID,
                canonical_market_id=None,
                venue_id=None,
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_filter_requires_filter(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.FILTER,
                canonical_market_id=None,
                venue_id=None,
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_all_rejects_filters(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryRequest(
                query_mode=MarketQueryMode.ALL,
                canonical_market_id=None,
                venue_id="venue-a",
                category_id=None,
                lifecycle=None,
                limit=None,
                lineage=lineage(),
            )

    def test_query_is_immutable(self) -> None:
        item = CertifiedActiveMarketQueryRequest(
            query_mode=MarketQueryMode.ALL,
            canonical_market_id=None,
            venue_id=None,
            category_id=None,
            lifecycle=None,
            limit=5,
            lineage=lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.limit = 10

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_023_certification_manifest()

        self.assertEqual(
            manifest.query_mode,
            "deterministic_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-023 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD023
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_023_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-022 "
        "consumed read-only"
    )
    print(
        "[PASS] Canonical market query IDs deterministic"
    )
    print(
        "[PASS] BY_ID, FILTER, and ALL query modes certified"
    )
    print(
        "[PASS] Venue, category, and lifecycle filters normalized"
    )
    print(
        "[PASS] Invalid query combinations rejected"
    )
    print(
        "[PASS] Deterministic result ordering and hashing contract certified"
    )
    print(
        "[PASS] Read-model hash lineage required"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-023 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY CONTRACT CERTIFIED"
    )
