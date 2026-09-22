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
from qseries_v2.universal_market_discovery.certified_incremental_discovery_admission_gate import (
    UMD_012_REVISION,
    CertifiedDiscoveryAdmissionDecision,
    build_umd_012_certification_manifest,
    certify_umd_012_foundation,
    verify_umd_012_certified_incremental_discovery_admission_gate,
)

FIXED = datetime(2026, 8, 5, 21, 30, tzinfo=timezone.utc)
BATCH_HASH = "a" * 64


def decision_lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-012",
        revision=UMD_012_REVISION,
        schema_version="1.0.0",
        parent_hashes=(BATCH_HASH,),
        source_refs=("fixture://umd-012/decision",),
        created_at=FIXED,
    )


class TestUMD012(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_012_foundation()["certified"])
        self.assertTrue(
            verify_umd_012_certified_incremental_discovery_admission_gate()
        )

    def test_admitted_decision_deterministic(self) -> None:
        checks = {
            "batch_id_not_seen": True,
            "batch_hash_not_seen": True,
        }
        first = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        second = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks=dict(reversed(tuple(checks.items()))),
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_rejected_decision_requires_matching_reasons(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=False,
                checks={"batch_id_not_seen": False},
                rejection_reasons=("wrong_reason",),
                lineage=decision_lineage(),
            )

    def test_admitted_decision_rejects_failed_checks(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=True,
                checks={"batch_id_not_seen": False},
                rejection_reasons=(),
                lineage=decision_lineage(),
            )

    def test_lineage_requires_batch_hash(self) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-012",
            revision=UMD_012_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-012/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=True,
                checks={"batch_id_not_seen": True},
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks={"batch_id_not_seen": True},
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.admitted = False
        with self.assertRaises(TypeError):
            item.checks["batch_id_not_seen"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_012_certification_manifest()
        self.assertEqual(manifest.gate_mode, "read_only_validation")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-012 CERTIFICATION TEST")
    print(" CERTIFIED INCREMENTAL DISCOVERY ADMISSION GATE")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD012)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_012_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-011 consumed read-only")
    print("[PASS] Admission decision IDs deterministic")
    print("[PASS] Admission and rejection states mutually consistent")
    print("[PASS] Rejection reasons bound to failed checks")
    print("[PASS] Batch-hash lineage requirement enforced")
    print("[PASS] Replay, cursor, sequence, and candidate checks registered")
    print("[PASS] Read-only admission gate certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-012 CERTIFIED INCREMENTAL DISCOVERY ADMISSION GATE CERTIFIED")
