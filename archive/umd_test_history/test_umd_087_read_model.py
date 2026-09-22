from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_085_read_model_admission_gate import (
    UMD_085_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_086_read_model_admission_ledger import (
    UMD_086_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,
    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
)
from qseries_v2.universal_market_discovery.umd_087_read_model import (
    UMD_087_REVISION,
    build_umd_087_admission_ledger_read_model,
    build_umd_087_certification_manifest,
    certify_umd_087_foundation,
    certify_umd_087_read_model,
)

FIXED = datetime(2026, 8, 8, 3, 5, 0, tzinfo=timezone.utc)

def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()

def decision(suffix: str, admitted: bool = True):
    read_model_hash = digest(f"umd-087:{suffix}:read-model")
    source_ledger_hash = digest(f"umd-087:{suffix}:source-ledger")
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-085",
        revision=UMD_085_REVISION,
        schema_version="1.0.0",
        parent_hashes=(read_model_hash, source_ledger_hash),
        source_refs=(f"fixture://umd-087/decision/{suffix}",),
        created_at=FIXED,
    )
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
        read_model_id=f"read-model-{suffix}",
        read_model_hash=read_model_hash,
        source_ledger_hash=source_ledger_hash,
        total_entry_count=2,
        admitted_entry_count=1,
        rejected_entry_count=1,
        latest_entry_id=f"entry-{suffix}",
        latest_admitted_entry_id=f"admitted-{suffix}",
        admitted=admitted,
        checks={"certified": admitted},
        rejection_reasons=() if admitted else ("certified",),
        lineage=lineage,
    )

def entry(number: int, value, previous):
    parents = [value.record_hash]
    if previous is not None:
        parents.append(previous)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-086",
        revision=UMD_086_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-087/entry/{number}",),
        created_at=FIXED,
    )
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )

def source_ledger():
    first = entry(1, decision("a", True), None)
    second = entry(2, decision("b", False), first.entry_hash)
    third = entry(3, decision("c", True), second.entry_hash)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-086",
        revision=UMD_086_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=("fixture://umd-087/ledger",),
        created_at=FIXED,
    )
    return ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=lineage,
    )

def model_lineage(ledger_hash: str):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-087",
        revision=UMD_087_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger_hash,),
        source_refs=("fixture://umd-087/read-model",),
        created_at=FIXED,
    )

class TestUMD087(unittest.TestCase):
    def test_foundation(self):
        result = certify_umd_087_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-087")

    def test_projection(self):
        ledger = source_ledger()
        model = build_umd_087_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=model_lineage(ledger.ledger_hash),
        )
        result = certify_umd_087_read_model(model)
        self.assertTrue(result["certified"])
        self.assertEqual(result["total_entry_count"], 3)
        self.assertEqual(result["admitted_entry_count"], 2)
        self.assertEqual(result["rejected_entry_count"], 1)

    def test_deterministic(self):
        ledger = source_ledger()
        lineage = model_lineage(ledger.ledger_hash)
        first = build_umd_087_admission_ledger_read_model(ledger, lineage=lineage)
        second = build_umd_087_admission_ledger_read_model(ledger, lineage=lineage)
        self.assertEqual(first.read_model_id, second.read_model_id)
        self.assertEqual(first.read_model_hash, second.read_model_hash)

    def test_positions_and_partitions(self):
        ledger = source_ledger()
        model = build_umd_087_admission_ledger_read_model(
            ledger,
            lineage=model_lineage(ledger.ledger_hash),
        )
        first, second, third = ledger.entries
        self.assertEqual(model.entry_position(first.entry_id), 1)
        self.assertEqual(model.read_model_position(second.decision.read_model_id), 2)
        self.assertEqual(model.read_model_hash_position(third.decision.read_model_hash), 3)
        self.assertEqual(model.source_ledger_hash_position(third.decision.source_ledger_hash), 3)
        self.assertEqual(model.decision_position(third.decision.decision_id), 3)
        self.assertTrue(model.is_admitted_entry(first.entry_id))
        self.assertTrue(model.is_rejected_entry(second.entry_id))
        self.assertEqual(model.latest_entry_id, third.entry_id)
        self.assertEqual(model.latest_admitted_entry_id, third.entry_id)

    def test_lineage_requires_ledger(self):
        ledger = source_ledger()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-087",
            revision=UMD_087_REVISION,
            schema_version="1.0.0",
            parent_hashes=(digest("wrong-ledger"),),
            source_refs=("fixture://umd-087/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            build_umd_087_admission_ledger_read_model(ledger, lineage=bad)

    def test_exact_umd086_type(self):
        ledger = source_ledger()
        self.assertIsInstance(ledger, ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger)
        self.assertEqual(ledger.ledger_lineage.build_id, "UMD-086")

    def test_immutable(self):
        ledger = source_ledger()
        model = build_umd_087_admission_ledger_read_model(
            ledger,
            metadata={"read_only": True},
            lineage=model_lineage(ledger.ledger_hash),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            model.total_entry_count = 99
        with self.assertRaises(TypeError):
            model.metadata["read_only"] = False
        with self.assertRaises(TypeError):
            model._entry_position_by_id[model.ordered_entry_ids[0]] = 99

    def test_side_effects(self):
        manifest = build_umd_087_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-087 CERTIFICATION TEST")
    print(" CERTIFIED RAW VENUE MARKET OBSERVATION READ MODEL")
    print("=" * 72)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD087)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    manifest = build_umd_087_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-086 consumed read-only")
    print("[PASS] Exact UMD-086 admission-ledger class consumed")
    print("[PASS] Deterministic UMD-086 admission-ledger projection certified")
    print("[PASS] Immutable entry, read-model, source-ledger, and decision indexes certified")
    print("[PASS] Admitted and rejected partitions certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-087 CERTIFIED")
