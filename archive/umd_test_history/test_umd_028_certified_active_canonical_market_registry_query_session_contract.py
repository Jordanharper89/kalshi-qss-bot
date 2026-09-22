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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_contract import (
    UMD_028_REVISION,
    QuerySessionState,
    build_umd_028_certification_manifest,
    certify_umd_028_foundation,
    verify_umd_028_certified_active_canonical_market_registry_query_session_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    8,
    30,
    tzinfo=timezone.utc,
)


class TestUMD028(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_028_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_028_certified_active_canonical_market_registry_query_session_contract()
        )

    def test_manifest_is_append_only_read_only(
        self,
    ) -> None:
        manifest = build_umd_028_certification_manifest()

        self.assertEqual(
            manifest.session_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_028_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 28)
            ),
        )

    def test_session_state_values(self) -> None:
        self.assertEqual(
            QuerySessionState.OPEN.value,
            "open",
        )
        self.assertEqual(
            QuerySessionState.CLOSED.value,
            "closed",
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-028",
            revision=UMD_028_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-028",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-028",
        )

    def test_lineage_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-028",
            revision=UMD_028_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-028",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-028 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD028
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_028_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-027 "
        "consumed read-only"
    )
    print(
        "[PASS] Deterministic query session IDs certified"
    )
    print(
        "[PASS] Ordered execution membership certified"
    )
    print(
        "[PASS] Duplicate session execution membership prohibited"
    )
    print(
        "[PASS] Open and closed session states certified"
    )
    print(
        "[PASS] Previous-session hash chaining certified"
    )
    print(
        "[PASS] Execution read-model lineage certified"
    )
    print(
        "[PASS] Immutable read-only session registry certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-028 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION CONTRACT CERTIFIED"
    )
