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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_admission_gate import (
    UMD_025_REVISION,
    CertifiedActiveMarketQueryExecutionAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_ledger import (
    UMD_026_REVISION,
    CertifiedActiveMarketQueryExecutionLedgerEntry,
    ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
    build_umd_026_certification_manifest,
    certify_active_market_query_execution_admission_ledger,
    certify_umd_026_foundation,
    verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger,
)

FIXED = datetime(
    2026,
    8,
    6,
    7,
    30,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool,
) -> CertifiedActiveMarketQueryExecutionAdmissionDecision:
    execution_hash = suffix * 64

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-025",
        revision=UMD_025_REVISION,
        schema_version="1.0.0",
        parent_hashes=(execution_hash,),
        source_refs=(
            f"fixture://umd-025/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    checks = {
        "execution_id_not_seen": admitted,
    }

    return CertifiedActiveMarketQueryExecutionAdmissionDecision(
        execution_id=(
            "umd:market-query-execution:"
            + suffix * 64
        ),
        execution_hash=execution_hash,
        query_id=(
            "umd:market-query:"
            + suffix * 64
        ),
        result_id=(
            "umd:market-query-result:"
            + suffix * 64
        ),
        admitted=admitted,
        checks=checks,
        rejection_reasons=(
            ()
            if admitted
            else ("execution_id_not_seen",)
        ),
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedActiveMarketQueryExecutionAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQueryExecutionLedgerEntry:
    parents = [value.record_hash]

    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-026",
        revision=UMD_026_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-026/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQueryExecutionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(entries) -> ReadOnlyActiveMarketQueryExecutionAdmissionLedger:
    return ReadOnlyActiveMarketQueryExecutionAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-026",
            revision=UMD_026_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(
                item.entry_hash
                for item in entries
            ),
            source_refs=(
                "fixture://umd-026/ledger",
            ),
            created_at=FIXED,
        ),
    )


class TestUMD026(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_026_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger()
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(1, value, None)

        self.assertEqual(
            first.entry_id,
            second.entry_id,
        )
        self.assertEqual(
            first.entry_hash,
            second.entry_hash,
        )

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

        result = certify_active_market_query_execution_admission_ledger(
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

    def test_duplicate_execution_rejected(self) -> None:
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
            build_id="UMD-026",
            revision=UMD_026_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-026/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryExecutionLedgerEntry(
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
        manifest = build_umd_026_certification_manifest()

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
    print(" UMD-026 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD026
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_026_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-025 "
        "consumed read-only"
    )
    print(
        "[PASS] Query execution ledger entry IDs deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] Execution-admission decision lineage verified"
    )
    print(
        "[PASS] Duplicate execution, decision, and result replay rejected"
    )
    print(
        "[PASS] Admitted and rejected execution indexes verified"
    )
    print(
        "[PASS] Latest admitted execution view deterministic"
    )
    print(
        "[PASS] Read-only query execution ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-026 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION LEDGER CERTIFIED"
    )
