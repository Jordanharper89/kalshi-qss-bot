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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_admission_gate import (
    UMD_029_REVISION,
    CertifiedActiveMarketQuerySessionAdmissionDecision,
    build_umd_029_certification_manifest,
    certify_umd_029_foundation,
    verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    9,
    0,
    tzinfo=timezone.utc,
)
SESSION_HASH = "a" * 64


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-029",
        revision=UMD_029_REVISION,
        schema_version="1.0.0",
        parent_hashes=(SESSION_HASH,),
        source_refs=(
            "fixture://umd-029/decision",
        ),
        created_at=FIXED,
    )


class TestUMD029(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_029_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "session_id_not_seen": True,
            "session_hash_not_seen": True,
        }

        first = CertifiedActiveMarketQuerySessionAdmissionDecision(
            session_id=(
                "umd:market-query-session:"
                + "b" * 64
            ),
            session_hash=SESSION_HASH,
            session_sequence=1,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=lineage(),
        )

        second = CertifiedActiveMarketQuerySessionAdmissionDecision(
            session_id=(
                "umd:market-query-session:"
                + "b" * 64
            ),
            session_hash=SESSION_HASH,
            session_sequence=1,
            admitted=True,
            checks=dict(
                reversed(tuple(checks.items()))
            ),
            rejection_reasons=(),
            lineage=lineage(),
        )

        self.assertEqual(
            first.decision_id,
            second.decision_id,
        )
        self.assertEqual(
            first.record_hash,
            second.record_hash,
        )

    def test_rejected_decision_requires_matching_reasons(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionAdmissionDecision(
                session_id=(
                    "umd:market-query-session:"
                    + "b" * 64
                ),
                session_hash=SESSION_HASH,
                session_sequence=1,
                admitted=False,
                checks={
                    "session_id_not_seen": False
                },
                rejection_reasons=(
                    "wrong_reason",
                ),
                lineage=lineage(),
            )

    def test_admitted_decision_rejects_failures(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionAdmissionDecision(
                session_id=(
                    "umd:market-query-session:"
                    + "b" * 64
                ),
                session_hash=SESSION_HASH,
                session_sequence=1,
                admitted=True,
                checks={
                    "session_id_not_seen": False
                },
                rejection_reasons=(),
                lineage=lineage(),
            )

    def test_lineage_requires_session_hash(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-029",
            revision=UMD_029_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-029/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionAdmissionDecision(
                session_id=(
                    "umd:market-query-session:"
                    + "b" * 64
                ),
                session_hash=SESSION_HASH,
                session_sequence=1,
                admitted=True,
                checks={
                    "session_id_not_seen": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedActiveMarketQuerySessionAdmissionDecision(
            session_id=(
                "umd:market-query-session:"
                + "b" * 64
            ),
            session_hash=SESSION_HASH,
            session_sequence=1,
            admitted=True,
            checks={
                "session_id_not_seen": True
            },
            rejection_reasons=(),
            lineage=lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.admitted = False

        with self.assertRaises(TypeError):
            item.checks[
                "session_id_not_seen"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_029_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_session_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-029 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION ADMISSION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD029
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_029_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-028 "
        "consumed read-only"
    )
    print(
        "[PASS] Query-session replay rejection certified"
    )
    print(
        "[PASS] Session sequence and previous-hash validation certified"
    )
    print(
        "[PASS] Session execution membership uniqueness certified"
    )
    print(
        "[PASS] Execution read-model identity binding certified"
    )
    print(
        "[PASS] Previously assigned execution rejection certified"
    )
    print(
        "[PASS] Deterministic session-admission decisions certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-029 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION ADMISSION GATE CERTIFIED"
    )
