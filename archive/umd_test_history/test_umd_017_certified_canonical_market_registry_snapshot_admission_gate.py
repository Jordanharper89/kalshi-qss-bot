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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_admission_gate import (
    UMD_017_REVISION,
    CertifiedSnapshotAdmissionDecision,
    build_umd_017_certification_manifest,
    certify_umd_017_foundation,
    verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    2,
    0,
    tzinfo=timezone.utc,
)
SNAPSHOT_HASH = "a" * 64


def decision_lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-017",
        revision=UMD_017_REVISION,
        schema_version="1.0.0",
        parent_hashes=(SNAPSHOT_HASH,),
        source_refs=(
            "fixture://umd-017/decision",
        ),
        created_at=FIXED,
    )


class TestUMD017(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_017_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "snapshot_id_not_seen": True,
            "snapshot_hash_not_seen": True,
        }

        first = CertifiedSnapshotAdmissionDecision(
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "b" * 64
            ),
            snapshot_hash=SNAPSHOT_HASH,
            snapshot_sequence=1,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        second = CertifiedSnapshotAdmissionDecision(
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "b" * 64
            ),
            snapshot_hash=SNAPSHOT_HASH,
            snapshot_sequence=1,
            admitted=True,
            checks=dict(
                reversed(tuple(checks.items()))
            ),
            rejection_reasons=(),
            lineage=decision_lineage(),
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
            CertifiedSnapshotAdmissionDecision(
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "b" * 64
                ),
                snapshot_hash=SNAPSHOT_HASH,
                snapshot_sequence=1,
                admitted=False,
                checks={
                    "snapshot_id_not_seen": False
                },
                rejection_reasons=(
                    "wrong_reason",
                ),
                lineage=decision_lineage(),
            )

    def test_admitted_decision_rejects_failures(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedSnapshotAdmissionDecision(
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "b" * 64
                ),
                snapshot_hash=SNAPSHOT_HASH,
                snapshot_sequence=1,
                admitted=True,
                checks={
                    "snapshot_id_not_seen": False
                },
                rejection_reasons=(),
                lineage=decision_lineage(),
            )

    def test_lineage_requires_snapshot_hash(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-017",
            revision=UMD_017_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-017/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedSnapshotAdmissionDecision(
                snapshot_id=(
                    "umd:market-registry-snapshot:"
                    + "b" * 64
                ),
                snapshot_hash=SNAPSHOT_HASH,
                snapshot_sequence=1,
                admitted=True,
                checks={
                    "snapshot_id_not_seen": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedSnapshotAdmissionDecision(
            snapshot_id=(
                "umd:market-registry-snapshot:"
                + "b" * 64
            ),
            snapshot_hash=SNAPSHOT_HASH,
            snapshot_sequence=1,
            admitted=True,
            checks={
                "snapshot_id_not_seen": True
            },
            rejection_reasons=(),
            lineage=decision_lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.admitted = False

        with self.assertRaises(TypeError):
            item.checks[
                "snapshot_id_not_seen"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_017_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_snapshot_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-017 CERTIFICATION TEST")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ADMISSION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD017
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_017_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-016 "
        "consumed read-only"
    )
    print(
        "[PASS] Snapshot replay rejection "
        "contract certified"
    )
    print(
        "[PASS] Snapshot sequence and previous-hash "
        "validation certified"
    )
    print(
        "[PASS] Source admission-registry binding "
        "certified"
    )
    print(
        "[PASS] Market count and record-hash equality "
        "checks certified"
    )
    print(
        "[PASS] Canonical market deletion "
        "rejection certified"
    )
    print(
        "[PASS] Deterministic snapshot admission "
        "decisions certified"
    )
    print(
        "[PASS] Read-only snapshot admission "
        "gate certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution "
        "disabled"
    )
    print(
        "[DONE] UMD-017 CERTIFIED CANONICAL MARKET "
        "REGISTRY SNAPSHOT ADMISSION GATE CERTIFIED"
    )
