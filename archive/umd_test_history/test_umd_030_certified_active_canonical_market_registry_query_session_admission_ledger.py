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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_admission_gate import (
    UMD_029_REVISION,
    CertifiedActiveMarketQuerySessionAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_admission_ledger import (
    UMD_030_REVISION,
    CertifiedActiveMarketQuerySessionAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionAdmissionLedger,
    build_umd_030_certification_manifest,
    certify_active_market_query_session_admission_ledger,
    certify_umd_030_foundation,
    verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger,
)

FIXED = datetime(
    2026,
    8,
    6,
    9,
    30,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool,
) -> CertifiedActiveMarketQuerySessionAdmissionDecision:
    session_hash = suffix * 64

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-029",
        revision=UMD_029_REVISION,
        schema_version="1.0.0",
        parent_hashes=(session_hash,),
        source_refs=(
            f"fixture://umd-029/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    checks = {
        "session_id_not_seen": admitted,
    }

    return CertifiedActiveMarketQuerySessionAdmissionDecision(
        session_id=(
            "umd:market-query-session:"
            + suffix * 64
        ),
        session_hash=session_hash,
        session_sequence=1,
        admitted=admitted,
        checks=checks,
        rejection_reasons=(
            ()
            if admitted
            else ("session_id_not_seen",)
        ),
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedActiveMarketQuerySessionAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQuerySessionAdmissionLedgerEntry:
    parents = [value.record_hash]

    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-030",
        revision=UMD_030_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-030/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(
    entries,
) -> ReadOnlyActiveMarketQuerySessionAdmissionLedger:
    return ReadOnlyActiveMarketQuerySessionAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-030",
            revision=UMD_030_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(
                item.entry_hash
                for item in entries
            ),
            source_refs=(
                "fixture://umd-030/ledger",
            ),
            created_at=FIXED,
        ),
    )


class TestUMD030(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_030_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger()
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

        result = certify_active_market_query_session_admission_ledger(
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

    def test_duplicate_session_rejected(self) -> None:
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
            build_id="UMD-030",
            revision=UMD_030_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-030/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionAdmissionLedgerEntry(
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
        manifest = build_umd_030_certification_manifest()

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
    print(" UMD-030 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION ADMISSION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD030
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_030_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-029 "
        "consumed read-only"
    )
    print(
        "[PASS] Query-session admission ledger entry IDs deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] Session-admission decision lineage verified"
    )
    print(
        "[PASS] Duplicate session and decision replay rejected"
    )
    print(
        "[PASS] Admitted and rejected session indexes verified"
    )
    print(
        "[PASS] Latest admitted session view deterministic"
    )
    print(
        "[PASS] Read-only session admission ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-030 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION ADMISSION LEDGER CERTIFIED"
    )
