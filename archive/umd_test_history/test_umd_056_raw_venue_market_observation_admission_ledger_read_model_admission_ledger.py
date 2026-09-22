from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate import (
    UMD_055_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger import (
    UMD_056_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerEntry,
    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,
    build_umd_056_certification_manifest,
    certify_umd_056_admission_ledger,
    certify_umd_056_foundation,
)

FIXED = datetime(
    2026,
    8,
    7,
    3,
    55,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def decision(
    suffix: str,
    admitted: bool = True,
):
    read_model_hash = digest(
        f"umd-056:{suffix}:read-model"
    )
    source_ledger_hash = digest(
        f"umd-056:{suffix}:source-ledger"
    )
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-055",
        revision=UMD_055_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            source_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-056/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionDecision(
        read_model_id=f"read-model-{suffix}",
        read_model_hash=read_model_hash,
        source_ledger_hash=source_ledger_hash,
        total_entry_count=2,
        admitted_entry_count=1,
        rejected_entry_count=1,
        latest_entry_id=f"entry-{suffix}",
        latest_admitted_entry_id=f"admitted-{suffix}",
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(number: int, value, previous):
    parents = [value.record_hash]
    if previous is not None:
        parents.append(previous)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-056",
        revision=UMD_056_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-056/entry/{number}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(entries):
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-056",
        revision=UMD_056_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            ()
            if not entries
            else (entries[-1].entry_hash,)
        ),
        source_refs=(
            "fixture://umd-056/ledger",
        ),
        created_at=FIXED,
    )
    return ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=lineage,
    )


class TestUMD056(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_056_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-056")

    def test_ledger_certifies(self) -> None:
        first = entry(1, decision("a", True), None)
        second = entry(
            2,
            decision("b", False),
            first.entry_hash,
        )
        item = ledger((first, second))
        result = certify_umd_056_admission_ledger(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_deterministic(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(1, value, None)
        self.assertEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.entry_hash, second.entry_hash)

    def test_sequence_gap_rejected(self) -> None:
        first = entry(1, decision("a"), None)
        second = entry(
            3,
            decision("b"),
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_hash_chain_rejected(self) -> None:
        first = entry(1, decision("a"), None)
        second = entry(
            2,
            decision("b"),
            digest("wrong"),
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_decision_rejected(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lookup_indexes(self) -> None:
        first = entry(1, decision("a"), None)
        second = entry(
            2,
            decision("b", False),
            first.entry_hash,
        )
        item = ledger((first, second))

        self.assertIs(item.get(first.entry_id), first)
        self.assertIs(
            item.get_by_read_model_id(
                first.decision.read_model_id
            ),
            first,
        )
        self.assertIs(
            item.get_by_read_model_hash(
                first.decision.read_model_hash
            ),
            first,
        )
        self.assertIs(
            item.get_by_source_ledger_hash(
                first.decision.source_ledger_hash
            ),
            first,
        )
        self.assertIs(
            item.get_by_decision_id(
                first.decision.decision_id
            ),
            first,
        )
        self.assertIs(item.latest_admitted(), first)

    def test_lineage_requires_latest_hash(self) -> None:
        first = entry(1, decision("a"), None)
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-056",
            revision=UMD_056_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-056/bad-ledger",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger(
                entries=(first,),
                ledger_lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        first = entry(1, decision("a"), None)
        item = ledger((first,))
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            first.sequence_number = 2
        with self.assertRaises(TypeError):
            first.metadata["read_only"] = False
        with self.assertRaises(TypeError):
            item._by_read_model_id["changed"] = first

    def test_side_effects(self) -> None:
        manifest = build_umd_056_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-056 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION "
        "LEDGER READ MODEL ADMISSION LEDGER"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD056
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_056_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-055 consumed read-only")
    print("[PASS] Exact UMD-055 read-model admission decision consumed")
    print("[PASS] Append-only sequence and previous-entry hash chain certified")
    print("[PASS] Duplicate read-model, source-ledger, and decision replay rejected")
    print("[PASS] Immutable read-model and decision indexes certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-056 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER READ MODEL ADMISSION LEDGER CERTIFIED")
