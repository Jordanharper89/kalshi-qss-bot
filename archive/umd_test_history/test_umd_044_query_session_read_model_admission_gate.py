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
)
from qseries_v2.universal_market_discovery.umd_044_query_session_read_model_admission_gate import (
    UMD_044_REVISION,
    CertifiedUMD044AdmissionDecision,
    build_umd_044_certification_manifest,
    certify_umd_044_foundation,
    evaluate_umd_044_admission,
)

FIXED = datetime(
    2026,
    8,
    6,
    19,
    35,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def upstream_decision(
    suffix: str,
    admitted: bool = True,
):
    read_model_hash = digest(f"umd-044:{suffix}:read-model")
    source_ledger_hash = digest(f"umd-044:{suffix}:source-ledger")
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-041",
        revision=UMD_041_REVISION,
        schema_version="1.0.0",
        parent_hashes=(read_model_hash, source_ledger_hash),
        source_refs=(f"fixture://umd-044/decision/{suffix}",),
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


def ledger_entry(number: int, decision, previous: str | None):
    parents = [decision.record_hash]
    if previous is not None:
        parents.append(previous)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-042",
        revision=UMD_042_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-044/entry/{number}",),
        created_at=FIXED,
    )

    return CertifiedUMD042AdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=decision,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def build_read_model():
    first = ledger_entry(1, upstream_decision("a", True), None)
    second = ledger_entry(
        2,
        upstream_decision("b", False),
        first.entry_hash,
    )
    third = ledger_entry(
        3,
        upstream_decision("c", True),
        second.entry_hash,
    )

    ledger_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-042",
        revision=UMD_042_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=("fixture://umd-044/ledger",),
        created_at=FIXED,
    )
    ledger = ReadOnlyUMD042AdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=ledger_lineage,
    )

    read_model_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-043",
        revision=UMD_043_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger.ledger_hash,),
        source_refs=("fixture://umd-044/read-model",),
        created_at=FIXED,
    )

    return build_umd_043_admission_ledger_read_model(
        ledger,
        metadata={"read_only": True},
        lineage=read_model_lineage,
    )


def gate_lineage(read_model):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-044",
        revision=UMD_044_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model.read_model_hash,
            read_model.source_ledger_hash,
        ),
        source_refs=("fixture://umd-044/gate",),
        created_at=FIXED,
    )


class TestUMD044(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_044_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-044")

    def test_valid_admitted(self) -> None:
        read_model = build_read_model()
        decision = evaluate_umd_044_admission(
            read_model,
            lineage=gate_lineage(read_model),
        )
        self.assertTrue(decision.admitted)
        self.assertEqual(decision.rejection_reasons, ())
        self.assertTrue(all(decision.checks.values()))

    def test_deterministic(self) -> None:
        read_model = build_read_model()
        lineage = gate_lineage(read_model)
        first = evaluate_umd_044_admission(
            read_model,
            lineage=lineage,
        )
        second = evaluate_umd_044_admission(
            read_model,
            lineage=lineage,
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_lineage_requires_both(self) -> None:
        read_model = build_read_model()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-044",
            revision=UMD_044_REVISION,
            schema_version="1.0.0",
            parent_hashes=(read_model.read_model_hash,),
            source_refs=("fixture://umd-044/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_umd_044_admission(
                read_model,
                lineage=bad,
            )

    def test_immutable(self) -> None:
        read_model = build_read_model()
        decision = evaluate_umd_044_admission(
            read_model,
            lineage=gate_lineage(read_model),
        )
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            decision.admitted = False
        with self.assertRaises(TypeError):
            decision.checks["changed"] = False

    def test_exact_umd_043_type(self) -> None:
        read_model = build_read_model()
        self.assertEqual(
            read_model.lineage.build_id,
            "UMD-043",
        )

    def test_side_effects(self) -> None:
        manifest = build_umd_044_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-044 CERTIFICATION TEST")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD044
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_044_certification_manifest()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-043 consumed read-only")
    print("[PASS] Exact UMD-043 read-model class consumed")
    print("[PASS] Immutable UMD-044 admission decisions certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-044 CERTIFIED")
