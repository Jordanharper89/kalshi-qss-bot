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
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_activation_gate import (
    UMD_020_REVISION,
    CertifiedSnapshotActivationDecision,
)
from qseries_v2.universal_market_discovery.certified_canonical_market_registry_snapshot_activation_ledger import (
    UMD_021_REVISION,
    CertifiedSnapshotActivationLedgerEntry,
    ReadOnlySnapshotActivationLedger,
    build_umd_021_certification_manifest,
    certify_snapshot_activation_ledger,
    certify_umd_021_foundation,
    verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    0,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool,
) -> CertifiedSnapshotActivationDecision:
    activation_hash = suffix * 64

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-020",
        revision=UMD_020_REVISION,
        schema_version="1.0.0",
        parent_hashes=(activation_hash,),
        source_refs=(
            f"fixture://umd-020/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    checks = {
        "activation_id_not_seen": admitted,
    }

    return CertifiedSnapshotActivationDecision(
        activation_id=(
            "umd:snapshot-activation:"
            + suffix * 64
        ),
        activation_hash=activation_hash,
        snapshot_id=(
            "umd:market-registry-snapshot:"
            + suffix * 64
        ),
        snapshot_hash=(
            ("f" if suffix != "f" else "e") * 64
        ),
        admitted=admitted,
        checks=checks,
        rejection_reasons=(
            ()
            if admitted
            else ("activation_id_not_seen",)
        ),
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedSnapshotActivationDecision,
    previous_entry_hash: str | None,
) -> CertifiedSnapshotActivationLedgerEntry:
    parents = [value.record_hash]

    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-021",
        revision=UMD_021_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-021/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedSnapshotActivationLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(entries) -> ReadOnlySnapshotActivationLedger:
    return ReadOnlySnapshotActivationLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-021",
            revision=UMD_021_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(
                item.entry_hash
                for item in entries
            ),
            source_refs=(
                "fixture://umd-021/ledger",
            ),
            created_at=FIXED,
        ),
    )


class TestUMD021(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_021_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger()
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(1, value, None)

        self.assertEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.entry_hash, second.entry_hash)

    def test_ledger_certifies(self) -> None:
        first = entry(
            1,
            decision("a", True),
            None,
        )
        second = entry(
            2,
            decision("b", False),
            first.entry_hash,
        )

        result = certify_snapshot_activation_ledger(
            ledger((second, first))
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_sequence_gap_rejected(self) -> None:
        first = entry(
            1,
            decision("a", True),
            None,
        )
        third = entry(
            3,
            decision("b", True),
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self) -> None:
        first = entry(
            1,
            decision("a", True),
            None,
        )
        second = entry(
            2,
            decision("b", True),
            "c" * 64,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_activation_rejected(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self) -> None:
        value = decision("a", True)

        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-021",
            revision=UMD_021_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-021/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedSnapshotActivationLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        item = entry(
            1,
            decision("a", True),
            None,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.sequence_number = 2

        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_021_certification_manifest()

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
    print(" UMD-021 CERTIFICATION TEST")
    print(
        " CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD021
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_021_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-020 "
        "consumed read-only"
    )
    print(
        "[PASS] Snapshot activation ledger entry IDs "
        "deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] Activation decision-to-ledger lineage verified"
    )
    print(
        "[PASS] Duplicate activation and decision replay rejected"
    )
    print(
        "[PASS] Admitted snapshot activation uniqueness enforced"
    )
    print(
        "[PASS] Latest admitted activation view deterministic"
    )
    print(
        "[PASS] Read-only activation ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-021 CERTIFIED CANONICAL MARKET REGISTRY "
        "SNAPSHOT ACTIVATION LEDGER CERTIFIED"
    )
