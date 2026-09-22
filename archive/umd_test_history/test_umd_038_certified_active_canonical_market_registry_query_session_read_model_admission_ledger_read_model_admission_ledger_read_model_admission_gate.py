from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate import (
    UMD_035_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger import (
    UMD_036_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model import (
    UMD_037_REVISION,
    build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate import (
    UMD_038_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,
    build_umd_038_certification_manifest,
    certify_umd_038_foundation,
    evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    6,
    45,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def admission_decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision:
    read_model_hash = digest(
        f"umd-038:{suffix}:read-model"
    )
    source_ledger_hash = digest(
        f"umd-038:{suffix}:source-ledger"
    )
    checks = {
        "certified": admitted,
    }
    reasons = (
        ()
        if admitted
        else ("certified",)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-035",
        revision=UMD_035_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            source_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-038/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        source_ledger_hash=source_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def ledger_entry(
    sequence_number: int,
    decision: CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry:
    parent_hashes = [decision.record_hash]
    if previous_entry_hash is not None:
        parent_hashes.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-036",
        revision=UMD_036_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parent_hashes),
        source_refs=(
            f"fixture://umd-038/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=decision,
        recorded_at=FIXED,
        metadata={
            "fixture": True,
            "read_only": True,
        },
        lineage=lineage,
    )


def build_source_ledger(
) -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger:
    first = ledger_entry(
        1,
        admission_decision("a", True),
        None,
    )
    second = ledger_entry(
        2,
        admission_decision("b", False),
        first.entry_hash,
    )
    third = ledger_entry(
        3,
        admission_decision("c", True),
        second.entry_hash,
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-036",
        revision=UMD_036_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            third.entry_hash,
        ),
        source_refs=(
            "fixture://umd-038/ledger",
        ),
        created_at=FIXED,
    )

    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(
        entries=(
            first,
            second,
            third,
        ),
        ledger_lineage=lineage,
    )


def build_model():
    ledger = build_source_ledger()

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-037",
        revision=UMD_037_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            ledger.ledger_hash,
        ),
        source_refs=(
            "fixture://umd-038/read-model",
        ),
        created_at=FIXED,
    )

    return build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
        ledger,
        metadata={
            "read_only": True,
        },
        lineage=lineage,
    )


def gate_lineage(model) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-038",
        revision=UMD_038_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            model.read_model_hash,
            model.source_ledger_hash,
        ),
        source_refs=(
            "fixture://umd-038/gate",
        ),
        created_at=FIXED,
    )


class TestUMD038(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        result = certify_umd_038_foundation()
        self.assertTrue(
            result["certified"]
        )
        self.assertEqual(
            result["build_id"],
            "UMD-038",
        )

    def test_valid_read_model_admitted(self) -> None:
        model = build_model()

        result = evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
            model,
            lineage=gate_lineage(model),
        )

        self.assertTrue(
            result.admitted
        )
        self.assertEqual(
            result.rejection_reasons,
            (),
        )
        self.assertTrue(
            all(result.checks.values())
        )

    def test_decision_identity_deterministic(self) -> None:
        model = build_model()
        lineage = gate_lineage(model)

        first = evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
            model,
            lineage=lineage,
        )
        second = evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
            model,
            lineage=lineage,
        )

        self.assertEqual(
            first.decision_id,
            second.decision_id,
        )
        self.assertEqual(
            first.record_hash,
            second.record_hash,
        )

    def test_decision_immutable(self) -> None:
        model = build_model()

        result = evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
            model,
            lineage=gate_lineage(model),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            result.admitted = False

        with self.assertRaises(TypeError):
            result.checks["changed"] = False

    def test_admitted_decision_rejects_failures(self) -> None:
        model = build_model()

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
                read_model_hash=model.read_model_hash,
                source_ledger_hash=model.source_ledger_hash,
                admitted=True,
                checks={
                    "bad": False,
                },
                rejection_reasons=(
                    "bad",
                ),
                lineage=gate_lineage(model),
            )

    def test_rejected_decision_requires_matching_reasons(
        self,
    ) -> None:
        model = build_model()

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
                read_model_hash=model.read_model_hash,
                source_ledger_hash=model.source_ledger_hash,
                admitted=False,
                checks={
                    "bad": False,
                },
                rejection_reasons=(
                    "different",
                ),
                lineage=gate_lineage(model),
            )

    def test_lineage_requires_both_parent_hashes(
        self,
    ) -> None:
        model = build_model()

        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-038",
            revision=UMD_038_REVISION,
            schema_version="1.0.0",
            parent_hashes=(
                model.read_model_hash,
            ),
            source_refs=(
                "fixture://umd-038/bad-lineage",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(
                model,
                lineage=bad_lineage,
            )

    def test_source_ledger_is_umd_036(self) -> None:
        ledger = build_source_ledger()

        self.assertIsInstance(
            ledger,
            ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,
        )
        self.assertEqual(
            ledger.ledger_lineage.build_id,
            "UMD-036",
        )

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_038_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "deterministic_read_only_admission",
        )
        self.assertFalse(
            manifest.network_enabled
        )
        self.assertFalse(
            manifest.persistence_enabled
        )
        self.assertFalse(
            manifest.mutation_enabled
        )
        self.assertFalse(
            manifest.publication_enabled
        )
        self.assertFalse(
            manifest.execution_enabled
        )


if __name__ == "__main__":
    print("=" * 96)
    print(" UMD-038 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER "
        "READ MODEL ADMISSION GATE"
    )
    print("=" * 96)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD038
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_038_certification_manifest()

    print()
    print(
        f"[PASS] Build: {manifest.build_id}"
    )
    print(
        f"[PASS] Revision: {manifest.revision}"
    )
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-037 consumed read-only"
    )
    print(
        "[PASS] UMD-035 decisions materialized into UMD-036 ledger"
    )
    print(
        "[PASS] UMD-036 ledger projected by UMD-037"
    )
    print(
        "[PASS] UMD-037 read-model deterministic identity certified"
    )
    print(
        "[PASS] Source UMD-036 ledger binding certified"
    )
    print(
        "[PASS] Counts, ordering, uniqueness, and partitions certified"
    )
    print(
        "[PASS] Latest-entry consistency certified"
    )
    print(
        "[PASS] Immutable UMD-038 admission decisions certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-038 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER READ MODEL "
        "ADMISSION LEDGER READ MODEL ADMISSION GATE CERTIFIED"
    )
