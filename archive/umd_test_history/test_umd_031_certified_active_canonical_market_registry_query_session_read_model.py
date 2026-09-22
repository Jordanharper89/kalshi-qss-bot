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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model import (
    UMD_031_REVISION,
    build_umd_031_certification_manifest,
    certify_umd_031_foundation,
    verify_umd_031_certified_active_canonical_market_registry_query_session_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    10,
    0,
    tzinfo=timezone.utc,
)


class TestUMD031(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_031_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_031_certified_active_canonical_market_registry_query_session_read_model()
        )

    def test_manifest_is_session_history_read_only(
        self,
    ) -> None:
        manifest = build_umd_031_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "session_history_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_031_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 31)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-031",
            revision=UMD_031_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-031",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-031",
        )

    def test_lineage_is_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-031",
            revision=UMD_031_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-031",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-031 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD031
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_031_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-030 "
        "consumed read-only"
    )
    print(
        "[PASS] Session registry and admission ledger binding certified"
    )
    print(
        "[PASS] Admitted and rejected session views certified"
    )
    print(
        "[PASS] Session ID and admission-entry indexes certified"
    )
    print(
        "[PASS] Execution-to-session membership index certified"
    )
    print(
        "[PASS] Latest admitted session view deterministic"
    )
    print(
        "[PASS] Immutable read-only session history certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-031 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL CERTIFIED"
    )
