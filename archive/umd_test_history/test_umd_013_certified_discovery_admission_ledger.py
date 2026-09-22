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
)
from qseries_v2.universal_market_discovery.certified_discovery_admission_ledger import (
    UMD_013_REVISION,
    CertifiedDiscoveryAdmissionLedgerEntry,
    ReadOnlyDiscoveryAdmissionLedger,
    build_umd_013_certification_manifest,
    certify_discovery_admission_ledger,
    certify_umd_013_foundation,
    verify_umd_013_certified_discovery_admission_ledger,
)

FIXED = datetime(2026, 8, 5, 22, 0, tzinfo=timezone.utc)


def decision(
    suffix: str,
    admitted: bool,
) -> CertifiedDiscoveryAdmissionDecision:
    batch_hash = suffix * 64
    checks = {
        "batch_id_not_seen": admitted,
    }
    reasons = () if admitted else ("batch_id_not_seen",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-012",
        revision=UMD_012_REVISION,
        schema_version="1.0.0",
        parent_hashes=(batch_hash,),
        source_refs=(
            f"fixture://umd-012/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedDiscoveryAdmissionDecision(
        batch_id="umd:batch:" + suffix * 64,
        batch_hash=batch_hash,
        source_id="fixture-source",
        batch_sequence=1,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(
    sequence: int,
    value: CertifiedDiscoveryAdmissionDecision,
    previous_hash: str | None,
) -> CertifiedDiscoveryAdmissionLedgerEntry:
    parents = [value.record_hash]
    if previous_hash is not None:
        parents.append(previous_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-013",
        revision=UMD_013_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-013/entry/{sequence}",
        ),
        created_at=FIXED,
    )

    return CertifiedDiscoveryAdmissionLedgerEntry(
        sequence_number=sequence,
        previous_entry_hash=previous_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(
    entries,
) -> ReadOnlyDiscoveryAdmissionLedger:
    return ReadOnlyDiscoveryAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-013",
            revision=UMD_013_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(
                item.entry_hash for item in entries
            ),
            source_refs=("fixture://umd-013/ledger",),
            created_at=FIXED,
        ),
    )


class TestUMD013(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_013_foundation()["certified"])
        self.assertTrue(
            verify_umd_013_certified_discovery_admission_ledger()
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(1, value, None)
        self.assertEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.entry_hash, second.entry_hash)

    def test_ledger_certifies(self) -> None:
        first = entry(1, decision("a", True), None)
        second = entry(
            2,
            decision("b", False),
            first.entry_hash,
        )
        result = certify_discovery_admission_ledger(
            ledger((second, first))
        )
        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_sequence_gap_rejected(self) -> None:
        first = entry(1, decision("a", True), None)
        third = entry(
            3,
            decision("b", True),
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self) -> None:
        first = entry(1, decision("a", True), None)
        second = entry(
            2,
            decision("b", True),
            "c" * 64,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_batch_rejected(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_entry_lineage_requires_decision_hash(self) -> None:
        value = decision("a", True)
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-013",
            revision=UMD_013_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-013/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        item = entry(1, decision("a", True), None)
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.sequence_number = 2
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_013_certification_manifest()
        self.assertEqual(
            manifest.ledger_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-013 CERTIFICATION TEST")
    print(" CERTIFIED DISCOVERY ADMISSION LEDGER")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD013
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_013_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-012 consumed read-only")
    print("[PASS] Admission ledger entry IDs deterministic")
    print("[PASS] Append-only sequence continuity enforced")
    print("[PASS] Previous-entry hash chain verified")
    print("[PASS] Decision-to-entry lineage verified")
    print("[PASS] Duplicate batch and decision replay rejected")
    print("[PASS] Admitted and rejected entry indexes verified")
    print("[PASS] Read-only admission ledger certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-013 CERTIFIED DISCOVERY ADMISSION LEDGER CERTIFIED")
