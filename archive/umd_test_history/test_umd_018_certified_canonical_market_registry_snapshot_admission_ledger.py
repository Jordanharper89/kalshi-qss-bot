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
)
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_admission_ledger import (
    UMD_018_REVISION,
    CertifiedSnapshotAdmissionLedgerEntry,
    ReadOnlySnapshotAdmissionLedger,
    build_umd_018_certification_manifest,
    certify_snapshot_admission_ledger,
    certify_umd_018_foundation,
    verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger,
)

FIXED = datetime(2026, 8, 6, 3, 0, tzinfo=timezone.utc)


def decision(suffix: str, admitted: bool) -> CertifiedSnapshotAdmissionDecision:
    snapshot_hash = suffix * 64
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-017",
        revision=UMD_017_REVISION,
        schema_version="1.0.0",
        parent_hashes=(snapshot_hash,),
        source_refs=(f"fixture://umd-017/decision/{suffix}",),
        created_at=FIXED,
    )
    checks = {"snapshot_id_not_seen": admitted}
    return CertifiedSnapshotAdmissionDecision(
        snapshot_id="umd:market-registry-snapshot:" + suffix * 64,
        snapshot_hash=snapshot_hash,
        snapshot_sequence=1,
        admitted=admitted,
        checks=checks,
        rejection_reasons=() if admitted else ("snapshot_id_not_seen",),
        lineage=lineage,
    )


def entry(sequence: int, value, previous_hash: str | None):
    parents = [value.record_hash]
    if previous_hash is not None:
        parents.append(previous_hash)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-018",
        revision=UMD_018_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-018/entry/{sequence}",),
        created_at=FIXED,
    )
    return CertifiedSnapshotAdmissionLedgerEntry(
        sequence_number=sequence,
        previous_entry_hash=previous_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(entries):
    return ReadOnlySnapshotAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-018",
            revision=UMD_018_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(item.entry_hash for item in entries),
            source_refs=("fixture://umd-018/ledger",),
            created_at=FIXED,
        ),
    )


class TestUMD018(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_018_foundation()["certified"])
        self.assertTrue(
            verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger()
        )

    def test_entry_identity_deterministic(self):
        value = decision("a", True)
        self.assertEqual(entry(1, value, None).entry_id, entry(1, value, None).entry_id)

    def test_ledger_certifies(self):
        first = entry(1, decision("a", True), None)
        second = entry(2, decision("b", False), first.entry_hash)
        result = certify_snapshot_admission_ledger(ledger((second, first)))
        self.assertTrue(result["certified"])
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_sequence_gap_rejected(self):
        first = entry(1, decision("a", True), None)
        third = entry(3, decision("b", True), first.entry_hash)
        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self):
        first = entry(1, decision("a", True), None)
        second = entry(2, decision("b", True), "c" * 64)
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_snapshot_rejected(self):
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(2, value, first.entry_hash)
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self):
        value = decision("a", True)
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-018",
            revision=UMD_018_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-018/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedSnapshotAdmissionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_immutable(self):
        item = entry(1, decision("a", True), None)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.sequence_number = 2
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self):
        manifest = build_umd_018_certification_manifest()
        self.assertEqual(manifest.ledger_mode, "append_only_read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-018 CERTIFICATION TEST")
    print(" CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT ADMISSION LEDGER")
    print("=" * 64)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD018)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_018_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-017 consumed read-only")
    print("[PASS] Snapshot admission ledger entry IDs deterministic")
    print("[PASS] Append-only sequence continuity enforced")
    print("[PASS] Previous-entry hash chain verified")
    print("[PASS] Decision-to-ledger lineage verified")
    print("[PASS] Duplicate snapshot and decision replay rejected")
    print("[PASS] Admitted and rejected snapshot indexes verified")
    print("[PASS] Read-only snapshot admission ledger certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-018 CERTIFIED CANONICAL MARKET REGISTRY SNAPSHOT ADMISSION LEDGER CERTIFIED")
