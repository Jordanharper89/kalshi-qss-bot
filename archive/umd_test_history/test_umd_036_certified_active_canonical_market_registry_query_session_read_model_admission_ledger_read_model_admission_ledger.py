from __future__ import annotations

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
    build_umd_036_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger,
    certify_umd_036_foundation,
)

FIXED = datetime(2026, 8, 6, 6, 35, 0, tzinfo=timezone.utc)


def decision(suffix: str, admitted: bool = True):
    read_model_hash = (suffix * 64)[:64]
    source_ledger_hash = (chr(ord(suffix) + 1) * 64)[:64]
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-035",
        revision=UMD_035_REVISION,
        schema_version="1.0.0",
        parent_hashes=(read_model_hash, source_ledger_hash),
        source_refs=(f"fixture://umd-036/decision/{suffix}",),
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


def entry(number, value, previous):
    parents = [value.record_hash]
    if previous is not None:
        parents.append(previous)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-036",
        revision=UMD_036_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-036/entry/{number}",),
        created_at=FIXED,
    )
    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(
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
        build_id="UMD-036",
        revision=UMD_036_REVISION,
        schema_version="1.0.0",
        parent_hashes=(() if not entries else (entries[-1].entry_hash,)),
        source_refs=("fixture://umd-036/ledger",),
        created_at=FIXED,
    )
    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=lineage,
    )


class TestUMD036(unittest.TestCase):
    def test_foundation_certifies(self):
        result = certify_umd_036_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-036")

    def test_entry_identity_deterministic(self):
        value = decision("a")
        first = entry(1, value, None)
        second = entry(1, value, None)
        self.assertEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.entry_hash, second.entry_hash)

    def test_ledger_certifies(self):
        first = entry(1, decision("a", True), None)
        second = entry(2, decision("d", False), first.entry_hash)
        item = ledger((first, second))
        result = certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_lookup_indexes(self):
        first = entry(1, decision("a"), None)
        item = ledger((first,))
        self.assertIs(item.get(first.entry_id), first)
        self.assertIs(
            item.get_by_read_model_hash(first.decision.read_model_hash),
            first,
        )
        self.assertIs(
            item.get_by_decision(first.decision.decision_id),
            first,
        )
        self.assertIs(item.latest_admitted(), first)

    def test_sequence_gap_rejected(self):
        first = entry(1, decision("a"), None)
        third = entry(3, decision("d"), first.entry_hash)
        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self):
        first = entry(1, decision("a"), None)
        second = entry(2, decision("d"), "f" * 64)
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_read_model_rejected(self):
        value = decision("a")
        first = entry(1, value, None)
        second = entry(2, value, first.entry_hash)
        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self):
        value = decision("a")
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-036",
            revision=UMD_036_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-036/bad-entry",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad,
            )

    def test_ledger_lineage_requires_latest_hash(self):
        first = entry(1, decision("a"), None)
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-036",
            revision=UMD_036_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-036/bad-ledger",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(
                entries=(first,),
                ledger_lineage=bad,
            )

    def test_immutable(self):
        first = entry(1, decision("a"), None)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            first.sequence_number = 2
        with self.assertRaises(TypeError):
            first.metadata["read_only"] = False

    def test_side_effects_disabled(self):
        manifest = build_umd_036_certification_manifest()
        self.assertEqual(manifest.ledger_mode, "append_only_read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 78)
    print(" UMD-036 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION READ MODEL "
        "ADMISSION LEDGER READ MODEL ADMISSION LEDGER"
    )
    print("=" * 78)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD036)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_036_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-035 consumed read-only")
    print("[PASS] UMD-035 admission decisions bound to ledger entries")
    print("[PASS] Entry IDs and record hashes deterministic")
    print("[PASS] Append-only sequence continuity enforced")
    print("[PASS] Previous-entry hash chain verified")
    print("[PASS] Duplicate read-model and decision replay rejected")
    print("[PASS] Admitted and rejected indexes verified")
    print("[PASS] Latest admitted view deterministic")
    print("[PASS] Immutable read-only admission ledger certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print(
        "[DONE] UMD-036 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY "
        "SESSION READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER CERTIFIED"
    )
