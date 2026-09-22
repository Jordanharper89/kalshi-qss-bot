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
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model import (
    UMD_034_REVISION,
    build_active_market_query_session_read_model_admission_ledger_read_model,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate import (
    UMD_035_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,
    build_umd_035_certification_manifest,
    certify_umd_035_foundation,
    evaluate_active_market_query_session_read_model_admission_ledger_read_model,
)

FIXED = datetime(2026, 8, 6, 6, 15, 0, tzinfo=timezone.utc)


def decision(suffix: str, admitted: bool = True):
    import hashlib
    hashes = tuple(
        hashlib.sha256(
            f"{suffix}:{offset}".encode("utf-8")
        ).hexdigest()
        for offset in range(3)
    )
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)
    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=hashes,
        source_refs=(f"fixture://umd-035/decision/{suffix}",),
        created_at=FIXED,
    )
    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=hashes[0],
        session_registry_hash=hashes[1],
        admission_ledger_hash=hashes[2],
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
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(f"fixture://umd-035/entry/{number}",),
        created_at=FIXED,
    )
    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=value,
        recorded_at=FIXED,
        metadata={"fixture": True},
        lineage=lineage,
    )


def build_model():
    first = entry(1, decision("a", True), None)
    second = entry(2, decision("d", False), first.entry_hash)
    third = entry(3, decision("g", True), second.entry_hash)
    ledger_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=("fixture://umd-035/ledger",),
        created_at=FIXED,
    )
    ledger = ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=ledger_lineage,
    )
    model_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-034",
        revision=UMD_034_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger.ledger_hash,),
        source_refs=("fixture://umd-035/read-model",),
        created_at=FIXED,
    )
    model = build_active_market_query_session_read_model_admission_ledger_read_model(
        ledger,
        metadata={"read_only": True},
        lineage=model_lineage,
    )
    return model


def gate_lineage(model):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-035",
        revision=UMD_035_REVISION,
        schema_version="1.0.0",
        parent_hashes=(model.read_model_hash, model.source_ledger_hash),
        source_refs=("fixture://umd-035/gate",),
        created_at=FIXED,
    )


class TestUMD035(unittest.TestCase):
    def test_foundation_certifies(self):
        result = certify_umd_035_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-035")

    def test_valid_read_model_admitted(self):
        model = build_model()
        result = evaluate_active_market_query_session_read_model_admission_ledger_read_model(
            model,
            lineage=gate_lineage(model),
        )
        self.assertTrue(result.admitted)
        self.assertEqual(result.rejection_reasons, ())
        self.assertTrue(all(result.checks.values()))

    def test_decision_identity_deterministic(self):
        model = build_model()
        lineage = gate_lineage(model)
        first = evaluate_active_market_query_session_read_model_admission_ledger_read_model(
            model,
            lineage=lineage,
        )
        second = evaluate_active_market_query_session_read_model_admission_ledger_read_model(
            model,
            lineage=lineage,
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_decision_immutable(self):
        model = build_model()
        result = evaluate_active_market_query_session_read_model_admission_ledger_read_model(
            model,
            lineage=gate_lineage(model),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            result.admitted = False
        with self.assertRaises(TypeError):
            result.checks["changed"] = False

    def test_admitted_decision_rejects_failures(self):
        model = build_model()
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision(
                read_model_hash=model.read_model_hash,
                source_ledger_hash=model.source_ledger_hash,
                admitted=True,
                checks={"bad": False},
                rejection_reasons=("bad",),
                lineage=gate_lineage(model),
            )

    def test_rejected_decision_requires_matching_reasons(self):
        model = build_model()
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision(
                read_model_hash=model.read_model_hash,
                source_ledger_hash=model.source_ledger_hash,
                admitted=False,
                checks={"bad": False},
                rejection_reasons=("other",),
                lineage=gate_lineage(model),
            )

    def test_lineage_requires_both_parent_hashes(self):
        model = build_model()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-035",
            revision=UMD_035_REVISION,
            schema_version="1.0.0",
            parent_hashes=(model.read_model_hash,),
            source_refs=("fixture://umd-035/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_active_market_query_session_read_model_admission_ledger_read_model(
                model,
                lineage=bad,
            )

    def test_side_effects_disabled(self):
        manifest = build_umd_035_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 76)
    print(" UMD-035 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION READ MODEL "
        "ADMISSION LEDGER READ MODEL ADMISSION GATE"
    )
    print("=" * 76)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD035)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_035_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-034 consumed read-only")
    print("[PASS] UMD-034 read-model deterministic identity certified")
    print("[PASS] Source UMD-033 ledger binding certified")
    print("[PASS] Counts, ordering, uniqueness, and partitions certified")
    print("[PASS] Latest-entry consistency certified")
    print("[PASS] Immutable admission decisions certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print(
        "[DONE] UMD-035 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY "
        "SESSION READ MODEL ADMISSION LEDGER READ MODEL ADMISSION GATE CERTIFIED"
    )
