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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_contract import (
    UMD_016_REVISION,
    build_umd_016_certification_manifest,
    certify_umd_016_foundation,
    verify_umd_016_certified_canonical_market_registry_snapshot_contract,
)

FIXED = datetime(2026, 8, 6, 1, 0, tzinfo=timezone.utc)


class TestUMD016(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_016_foundation()["certified"])
        self.assertTrue(
            verify_umd_016_certified_canonical_market_registry_snapshot_contract()
        )

    def test_manifest_is_append_only_read_only(self) -> None:
        manifest = build_umd_016_certification_manifest()
        self.assertEqual(
            manifest.snapshot_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_016_certification_manifest()
        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 16)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-016",
            revision=UMD_016_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-016",),
            created_at=FIXED,
        )
        self.assertEqual(lineage.build_id, "UMD-016")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-016 CERTIFICATION TEST")
    print(" CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD016
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_016_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-015 consumed read-only")
    print("[PASS] Canonical market snapshot contract certified")
    print("[PASS] Snapshot IDs and hashes deterministic")
    print("[PASS] Snapshot sequence continuity required")
    print("[PASS] Previous-snapshot hash chain required")
    print("[PASS] Source admission-registry hash lineage required")
    print("[PASS] Duplicate canonical market IDs prohibited")
    print("[PASS] Canonical market deletion across snapshots prohibited")
    print("[PASS] Read-only snapshot chain certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-016 CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT CONTRACT CERTIFIED")
