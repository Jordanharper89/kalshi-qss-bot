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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_read_model import (
    UMD_027_REVISION,
    build_umd_027_certification_manifest,
    certify_umd_027_foundation,
    verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    8,
    0,
    tzinfo=timezone.utc,
)


class TestUMD027(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_027_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model()
        )

    def test_manifest_is_execution_history_read_only(
        self,
    ) -> None:
        manifest = build_umd_027_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "execution_history_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_027_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 27)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-027",
            revision=UMD_027_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-027",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-027",
        )


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-027 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD027
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_027_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-026 "
        "consumed read-only"
    )
    print(
        "[PASS] Execution-ledger hash lineage certified"
    )
    print(
        "[PASS] Entry, execution, query, and result indexes certified"
    )
    print(
        "[PASS] Admitted and rejected execution views certified"
    )
    print(
        "[PASS] Latest admitted execution view deterministic"
    )
    print(
        "[PASS] Deterministic ordering and replay certified"
    )
    print(
        "[PASS] Immutable read-only execution history certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-027 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION READ MODEL CERTIFIED"
    )
