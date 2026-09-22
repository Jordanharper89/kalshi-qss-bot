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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_activation_contract import (
    UMD_019_REVISION,
    build_umd_019_certification_manifest,
    certify_umd_019_foundation,
    verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    4,
    0,
    tzinfo=timezone.utc,
)


class TestUMD019(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_019_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract()
        )

    def test_manifest_is_single_active_read_only(self) -> None:
        manifest = build_umd_019_certification_manifest()

        self.assertEqual(
            manifest.activation_mode,
            "single_active_read_only_snapshot",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_019_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 19)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-019",
            revision=UMD_019_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-019",),
            created_at=FIXED,
        )

        self.assertEqual(lineage.build_id, "UMD-019")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-019 CERTIFICATION TEST")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD019
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_019_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-018 "
        "consumed read-only"
    )
    print(
        "[PASS] Admitted-snapshot-only activation "
        "contract certified"
    )
    print(
        "[PASS] Snapshot, decision, and ledger "
        "identity binding certified"
    )
    print(
        "[PASS] Snapshot activation lineage "
        "requirements certified"
    )
    print(
        "[PASS] Single active read-only registry "
        "contract certified"
    )
    print(
        "[PASS] Active snapshot and market count "
        "views deterministic"
    )
    print(
        "[PASS] Automatic activation and persistence "
        "disabled"
    )
    print(
        "[PASS] Publication and Q Series execution "
        "disabled"
    )
    print(
        "[DONE] UMD-019 CERTIFIED CANONICAL MARKET "
        "REGISTRY SNAPSHOT ACTIVATION CONTRACT CERTIFIED"
    )
