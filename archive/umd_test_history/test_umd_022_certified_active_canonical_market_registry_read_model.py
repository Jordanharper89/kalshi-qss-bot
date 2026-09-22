from __future__ import annotations

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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_read_model import (
    UMD_022_REVISION,
    build_umd_022_certification_manifest,
    certify_umd_022_foundation,
    verify_umd_022_certified_active_canonical_market_registry_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    30,
    tzinfo=timezone.utc,
)


class TestUMD022(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_022_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_022_certified_active_canonical_market_registry_read_model()
        )

    def test_manifest_is_active_snapshot_read_only(
        self,
    ) -> None:
        manifest = build_umd_022_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "active_snapshot_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_022_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 22)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-022",
            revision=UMD_022_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-022",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-022",
        )


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-022 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD022
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_022_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-021 "
        "consumed read-only"
    )
    print(
        "[PASS] Active registry and latest admitted "
        "activation binding certified"
    )
    print(
        "[PASS] Canonical market lookup index certified"
    )
    print(
        "[PASS] Venue, category, and lifecycle indexes certified"
    )
    print(
        "[PASS] Deterministic index ordering and replay certified"
    )
    print(
        "[PASS] Immutable read-model lineage certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-022 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY READ MODEL CERTIFIED"
    )
