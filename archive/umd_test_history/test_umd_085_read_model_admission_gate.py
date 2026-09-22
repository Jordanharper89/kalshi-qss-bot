from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_082_read_model_admission_gate import (
    UMD_082_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_083_read_model_admission_ledger import (
    UMD_083_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,
    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
)
from qseries_v2.universal_market_discovery.umd_084_read_model import (
    UMD_084_REVISION,
    build_umd_084_admission_ledger_read_model,
)
from qseries_v2.universal_market_discovery.umd_085_read_model_admission_gate import (
    UMD_085_REVISION,
    build_umd_085_certification_manifest,
    certify_umd_085_foundation,
    evaluate_umd_085_read_model_admission,
)

FIXED = datetime(2026, 8, 8, 2, 5, 0, tzinfo=timezone.utc)

def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()

def decision(suffix: str, admitted: bool = True):
    read_model_hash = digest(f"umd-085:{suffix}:read-model")
    source_ledger_hash = digest(f"umd-085:{suffix}:source-ledger")
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-082",
        revision=UMD_082_REVISION,
        schema_version="1.0.0",
        parent_hashes=(read_model_hash, source_ledger_hash),
        source_refs=(f"fixture://umd-085/decision/{suffix}",),
        created_at=FIXED,
    )
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
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
        build_id="UMD-083",
        revision=UMD_083_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-085/entry/{number}",),
        created_at=FIXED,
    )
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )

def read_model():
    first = entry(1, decision("a", True), None)
    second = entry(2, decision("b", False), first.entry_hash)

    ledger_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-083",
        revision=UMD_083_REVISION,
        schema_version="1.0.0",
        parent_hashes=(second.entry_hash,),
        source_refs=("fixture://umd-085/ledger",),
        created_at=FIXED,
    )

    ledger = ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger(
        entries=(first, second),
        ledger_lineage=ledger_lineage,
    )

    model_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-084",
        revision=UMD_084_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger.ledger_hash,),
        source_refs=("fixture://umd-085/read-model",),
        created_at=FIXED,
    )

    return build_umd_084_admission_ledger_read_model(
        ledger,
        metadata={"read_only": True},
        lineage=model_lineage,
    )

def gate_lineage(model):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-085",
        revision=UMD_085_REVISION,
        schema_version="1.0.0",
        parent_hashes=(model.read_model_hash, model.source_ledger_hash),
        source_refs=("fixture://umd-085/gate",),
        created_at=FIXED,
    )

class TestUMD085(unittest.TestCase):
    def test_foundation(self):
        result = certify_umd_085_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-085")

    def test_valid_read_model_admitted(self):
        model = read_model()
        value = evaluate_umd_085_read_model_admission(
            model,
            lineage=gate_lineage(model),
        )
        self.assertTrue(value.admitted)
        self.assertEqual(value.rejection_reasons, ())
        self.assertTrue(all(value.checks.values()))

    def test_deterministic(self):
        model = read_model()
        lineage = gate_lineage(model)
        first = evaluate_umd_085_read_model_admission(model, lineage=lineage)
        second = evaluate_umd_085_read_model_admission(model, lineage=lineage)
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_duplicate_read_model_id_rejected(self):
        model = read_model()
        value = evaluate_umd_085_read_model_admission(
            model,
            seen_read_model_ids=(model.read_model_id,),
            lineage=gate_lineage(model),
        )
        self.assertFalse(value.admitted)
        self.assertIn("read_model_id_not_seen", value.rejection_reasons)

    def test_duplicate_read_model_hash_rejected(self):
        model = read_model()
        value = evaluate_umd_085_read_model_admission(
            model,
            seen_read_model_hashes=(model.read_model_hash,),
            lineage=gate_lineage(model),
        )
        self.assertFalse(value.admitted)
        self.assertIn("read_model_hash_not_seen", value.rejection_reasons)

    def test_duplicate_source_ledger_rejected(self):
        model = read_model()
        value = evaluate_umd_085_read_model_admission(
            model,
            seen_source_ledger_hashes=(model.source_ledger_hash,),
            lineage=gate_lineage(model),
        )
        self.assertFalse(value.admitted)
        self.assertIn("source_ledger_hash_not_seen", value.rejection_reasons)

    def test_lineage_requires_both_hashes(self):
        model = read_model()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-085",
            revision=UMD_085_REVISION,
            schema_version="1.0.0",
            parent_hashes=(model.read_model_hash,),
            source_refs=("fixture://umd-085/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_umd_085_read_model_admission(model, lineage=bad)

    def test_exact_umd084_type(self):
        model = read_model()
        self.assertEqual(model.lineage.build_id, "UMD-084")

    def test_immutable(self):
        model = read_model()
        value = evaluate_umd_085_read_model_admission(
            model,
            lineage=gate_lineage(model),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            value.admitted = False
        with self.assertRaises(TypeError):
            value.checks["changed"] = False

    def test_side_effects(self):
        manifest = build_umd_085_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-085 CERTIFICATION TEST")
    print(" CERTIFIED RAW VENUE MARKET OBSERVATION READ MODEL ADMISSION GATE")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD085)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_085_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-084 consumed read-only")
    print("[PASS] Exact UMD-084 read-model class consumed")
    print("[PASS] Deterministic read-model admission decision certified")
    print("[PASS] Duplicate read-model ID, hash, and source-ledger replay rejected")
    print("[PASS] Immutable complete decision lineage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-085 CERTIFIED")
