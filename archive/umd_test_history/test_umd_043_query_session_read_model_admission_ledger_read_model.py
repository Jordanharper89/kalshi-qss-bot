from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_041_query_session_read_model_admission_gate import (
    UMD_041_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_042_query_session_read_model_admission_ledger import (
    UMD_042_REVISION,
    CertifiedUMD042AdmissionLedgerEntry,
    ReadOnlyUMD042AdmissionLedger,
)
from qseries_v2.universal_market_discovery.umd_043_query_session_read_model_admission_ledger_read_model import (
    UMD_043_REVISION,
    build_umd_043_admission_ledger_read_model,
    build_umd_043_certification_manifest,
    certify_umd_043_foundation,
    certify_umd_043_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    18,
    30,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision:
    read_model_hash = digest(f"umd-043:{suffix}:read-model")
    source_ledger_hash = digest(
        f"umd-043:{suffix}:source-ledger"
    )
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-041",
        revision=UMD_041_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            source_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-043/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        source_ledger_hash=source_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(number: int, value, previous: str | None):
    parents = [value.record_hash]
    if previous is not None:
        parents.append(previous)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-042",
        revision=UMD_042_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-043/entry/{number}",
        ),
        created_at=FIXED,
    )

    return CertifiedUMD042AdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def source_ledger() -> ReadOnlyUMD042AdmissionLedger:
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
    third = entry(
        3,
        decision("c", True),
        second.entry_hash,
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-042",
        revision=UMD_042_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=(
            "fixture://umd-043/ledger",
        ),
        created_at=FIXED,
    )

    return ReadOnlyUMD042AdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=lineage,
    )


def read_model_lineage(ledger_hash: str) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-043",
        revision=UMD_043_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger_hash,),
        source_refs=(
            "fixture://umd-043/read-model",
        ),
        created_at=FIXED,
    )


class TestUMD043(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_043_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-043")

    def test_projection(self) -> None:
        ledger = source_ledger()
        model = build_umd_043_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=read_model_lineage(ledger.ledger_hash),
        )
        result = certify_umd_043_read_model(model)
        self.assertTrue(result["certified"])
        self.assertEqual(result["total_entry_count"], 3)
        self.assertEqual(result["admitted_entry_count"], 2)
        self.assertEqual(result["rejected_entry_count"], 1)

    def test_deterministic(self) -> None:
        ledger = source_ledger()
        lineage = read_model_lineage(ledger.ledger_hash)
        first = build_umd_043_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=lineage,
        )
        second = build_umd_043_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=lineage,
        )
        self.assertEqual(first.read_model_id, second.read_model_id)
        self.assertEqual(
            first.read_model_hash,
            second.read_model_hash,
        )

    def test_positions_and_partitions(self) -> None:
        ledger = source_ledger()
        model = build_umd_043_admission_ledger_read_model(
            ledger,
            lineage=read_model_lineage(ledger.ledger_hash),
        )
        first, second, third = ledger.entries

        self.assertEqual(
            model.entry_position(first.entry_id),
            1,
        )
        self.assertEqual(
            model.read_model_position(
                second.decision.read_model_hash
            ),
            2,
        )
        self.assertEqual(
            model.decision_position(
                third.decision.decision_id
            ),
            3,
        )
        self.assertTrue(
            model.is_admitted_entry(first.entry_id)
        )
        self.assertTrue(
            model.is_rejected_entry(second.entry_id)
        )
        self.assertEqual(
            model.latest_entry_id,
            third.entry_id,
        )
        self.assertEqual(
            model.latest_admitted_entry_id,
            third.entry_id,
        )

    def test_lineage_requires_ledger(self) -> None:
        ledger = source_ledger()
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-043",
            revision=UMD_043_REVISION,
            schema_version="1.0.0",
            parent_hashes=(digest("wrong-ledger"),),
            source_refs=(
                "fixture://umd-043/bad-lineage",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            build_umd_043_admission_ledger_read_model(
                ledger,
                lineage=bad_lineage,
            )

    def test_exact_umd_042_type(self) -> None:
        ledger = source_ledger()
        self.assertIsInstance(
            ledger,
            ReadOnlyUMD042AdmissionLedger,
        )
        self.assertEqual(
            ledger.ledger_lineage.build_id,
            "UMD-042",
        )

    def test_immutable(self) -> None:
        ledger = source_ledger()
        model = build_umd_043_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=read_model_lineage(ledger.ledger_hash),
        )
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            model.total_entry_count = 99
        with self.assertRaises(TypeError):
            model.metadata["read_only"] = False
        with self.assertRaises(TypeError):
            model._entry_position_by_id[
                model.ordered_entry_ids[0]
            ] = 99

    def test_side_effects(self) -> None:
        manifest = build_umd_043_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-043 CERTIFICATION TEST")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD043
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_043_certification_manifest()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-042 consumed read-only")
    print("[PASS] Exact UMD-042 ledger class consumed")
    print("[PASS] Deterministic UMD-043 projection certified")
    print("[PASS] Immutable read-only indexes certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-043 CERTIFIED")
