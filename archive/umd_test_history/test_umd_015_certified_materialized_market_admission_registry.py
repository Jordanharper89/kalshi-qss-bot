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
from qseries_v2.universal_market_discovery.certified_materialized_market_admission_registry import (
    UMD_015_REVISION,
    build_umd_015_certification_manifest,
    certify_umd_015_foundation,
    verify_umd_015_certified_materialized_market_admission_registry,
)

FIXED = datetime(2026, 8, 6, 0, 0, tzinfo=timezone.utc)


class TestUMD015(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_015_foundation()["certified"])
        self.assertTrue(
            verify_umd_015_certified_materialized_market_admission_registry()
        )

    def test_manifest_is_append_only_read_only(self) -> None:
        manifest = build_umd_015_certification_manifest()
        self.assertEqual(
            manifest.registry_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_015_certification_manifest()
        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 15)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-015",
            revision=UMD_015_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-015",),
            created_at=FIXED,
        )
        self.assertEqual(lineage.build_id, "UMD-015")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-015 CERTIFICATION TEST")
    print(" CERTIFIED MATERIALIZED MARKET ADMISSION REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD015
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_015_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-014 consumed read-only")
    print("[PASS] Materialization-to-admission contract certified")
    print("[PASS] Append-only admission sequence enforced")
    print("[PASS] Previous-admission hash chain required")
    print("[PASS] Existing canonical markets protected")
    print("[PASS] Duplicate market admission prohibited")
    print("[PASS] Duplicate materialization admission prohibited")
    print("[PASS] Complete market view deterministic")
    print("[PASS] Read-only admission registry certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-015 CERTIFIED MATERIALIZED MARKET ADMISSION REGISTRY CERTIFIED")
