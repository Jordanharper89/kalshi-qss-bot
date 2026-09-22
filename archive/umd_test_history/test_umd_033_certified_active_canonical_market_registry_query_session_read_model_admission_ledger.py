from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger import (
    UMD_033_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
    build_umd_033_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger,
    certify_umd_033_foundation,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    30,
    0,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash = (
        suffix.lower() * 64
    )[:64]
    session_registry_hash = (
        chr(ord(suffix.lower()) + 1) * 64
    )[:64]
    admission_ledger_hash = (
        chr(ord(suffix.lower()) + 2) * 64
    )[:64]

    checks = {
        "read_model_hash_deterministic": admitted,
    }
    reasons = (
        ()
        if admitted
        else ("read_model_hash_deterministic",)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            session_registry_hash,
            admission_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-033/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        session_registry_hash=session_registry_hash,
        admission_ledger_hash=admission_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry:
    parents = [value.record_hash]
    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-033/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={
            "read_only": True,
            "source": "certification-fixture",
        },
        lineage=lineage,
    )


def ledger(
    entries: tuple[
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
        ...
    ],
) -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger:
    parent_hashes = (
        ()
        if not entries
        else (entries[-1].entry_hash,)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(
            "fixture://umd-033/ledger",
        ),
        created_at=FIXED,
    )

    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
        entries=entries,
        ledger_lineage=lineage,
    )


class TestUMD033(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        result = certify_umd_033_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(
            result["build_id"],
            "UMD-033",
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a")
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
            decision("a"),
            None,
        )
        second = entry(
            2,
            decision("d", admitted=False),
            first.entry_hash,
        )
        item = ledger((first, second))

        result = (
            certify_active_market_query_session_read_model_admission_ledger(
                item
            )
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_lookup_indexes(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        item = ledger((first,))

        self.assertIs(
            item.get(first.entry_id),
            first,
        )
        self.assertIs(
            item.get_by_read_model_hash(
                first.decision.read_model_hash
            ),
            first,
        )
        self.assertIs(
            item.get_by_decision(
                first.decision.decision_id
            ),
            first,
        )
        self.assertIs(
            item.latest_admitted(),
            first,
        )

    def test_sequence_gap_rejected(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        third = entry(
            3,
            decision("d"),
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        second = entry(
            2,
            decision("d"),
            "f" * 64,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_read_model_rejected(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self) -> None:
        value = decision("a")

        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-033",
            revision=UMD_033_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-033/bad-entry",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_ledger_lineage_requires_latest_hash(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-033",
            revision=UMD_033_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-033/bad-ledger",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
                entries=(first,),
                ledger_lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            first.sequence_number = 2

        with self.assertRaises(TypeError):
            first.metadata["read_only"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_033_certification_manifest()

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
    print(" UMD-033 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD033
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_033_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-032 "
        "consumed read-only"
    )
    print(
        "[PASS] Read-model admission ledger entry IDs deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] UMD-032 decision-to-ledger lineage verified"
    )
    print(
        "[PASS] Duplicate read-model and decision replay rejected"
    )
    print(
        "[PASS] Admitted and rejected read-model indexes verified"
    )
    print(
        "[PASS] Latest admitted read-model view deterministic"
    )
    print(
        "[PASS] Immutable read-only admission ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-033 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL ADMISSION LEDGER CERTIFIED"
    )
