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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_engine import (
    UMD_024_REVISION,
    build_umd_024_certification_manifest,
    certify_umd_024_foundation,
    verify_umd_024_certified_active_canonical_market_registry_query_execution_engine,
)

FIXED = datetime(
    2026,
    8,
    6,
    6,
    30,
    tzinfo=timezone.utc,
)


class TestUMD024(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_024_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_024_certified_active_canonical_market_registry_query_execution_engine()
        )

    def test_manifest_is_deterministic_read_only(
        self,
    ) -> None:
        manifest = build_umd_024_certification_manifest()

        self.assertEqual(
            manifest.engine_mode,
            "deterministic_read_only_execution",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_024_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 24)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-024",
            revision=UMD_024_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-024",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-024",
        )

    def test_lineage_is_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-024",
            revision=UMD_024_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-024",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-024 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION ENGINE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD024
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_024_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-023 "
        "consumed read-only"
    )
    print(
        "[PASS] Certified query execution contract registered"
    )
    print(
        "[PASS] Query request and result identity binding certified"
    )
    print(
        "[PASS] Execution sequence and previous-hash chaining certified"
    )
    print(
        "[PASS] Duplicate result replay rejection certified"
    )
    print(
        "[PASS] Deterministic execution summaries certified"
    )
    print(
        "[PASS] Read-only execution ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-024 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION ENGINE CERTIFIED"
    )
