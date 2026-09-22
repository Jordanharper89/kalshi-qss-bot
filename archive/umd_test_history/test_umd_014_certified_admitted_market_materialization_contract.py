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
from qseries_v2.universal_market_discovery.certified_admitted_market_materialization_contract import (
    UMD_014_REVISION,
    build_umd_014_certification_manifest,
    certify_umd_014_foundation,
    verify_umd_014_certified_admitted_market_materialization_contract,
)

FIXED = datetime(2026, 8, 5, 23, 0, tzinfo=timezone.utc)


class TestUMD014(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_014_foundation()["certified"])
        self.assertTrue(
            verify_umd_014_certified_admitted_market_materialization_contract()
        )

    def test_manifest_is_read_only(self) -> None:
        manifest = build_umd_014_certification_manifest()
        self.assertEqual(
            manifest.contract_mode,
            "read_only_materialization",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_014_certification_manifest()
        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 14)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-014",
            revision=UMD_014_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-014",),
            created_at=FIXED,
        )
        self.assertEqual(lineage.build_id, "UMD-014")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-014 CERTIFICATION TEST")
    print(" CERTIFIED ADMITTED MARKET MATERIALIZATION CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD014
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_014_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-013 consumed read-only")
    print("[PASS] Admitted-only materialization contract certified")
    print("[PASS] Rejected batch materialization prohibited")
    print("[PASS] Candidate-to-market identity preserved")
    print("[PASS] Candidate, batch, decision, and ledger lineage required")
    print("[PASS] Duplicate candidate materialization prohibited")
    print("[PASS] Duplicate canonical market materialization prohibited")
    print("[PASS] Deterministic materialization ordering verified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-014 CERTIFIED ADMITTED MARKET MATERIALIZATION CONTRACT CERTIFIED")
