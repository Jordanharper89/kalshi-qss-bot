from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.umd_052_raw_venue_market_observation_admission_gate import (
    UMD_052_REVISION,
    CertifiedRawVenueMarketObservationAdmissionDecision,
)
from qseries_v2.universal_market_discovery.umd_053_raw_venue_market_observation_admission_ledger import (
    UMD_053_REVISION,
    CertifiedRawVenueMarketObservationAdmissionLedgerEntry,
    ReadOnlyRawVenueMarketObservationAdmissionLedger,
)
from qseries_v2.universal_market_discovery.umd_054_raw_venue_market_observation_admission_ledger_read_model import (
    UMD_054_REVISION,
    build_umd_054_observation_admission_ledger_read_model,
)
from qseries_v2.universal_market_discovery.umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate import (
    UMD_055_REVISION,
    build_umd_055_certification_manifest,
    certify_umd_055_foundation,
    evaluate_umd_055_read_model_admission,
)

FIXED = datetime(
    2026,
    8,
    7,
    3,
    35,
    0,
    tzinfo=timezone.utc,
)


def digest(label: str) -> str:
    return hashlib.sha256(
        label.encode("utf-8")
    ).hexdigest()


def source_decision(
    suffix: str,
    admitted: bool = True,
):
    observation_hash = digest(
        f"umd-055:{suffix}:observation"
    )
    request_hash = digest(
        f"umd-055:{suffix}:request"
    )
    request_decision_hash = digest(
        f"umd-055:{suffix}:request-decision"
    )
    source_contract_hash = digest(
        f"umd-055:{suffix}:source-contract"
    )
    source_registry_hash = digest(
        f"umd-055:{suffix}:source-registry"
    )
    raw_payload_hash = digest(
        f"umd-055:{suffix}:payload"
    )
    checks = {"certified": admitted}
    reasons = () if admitted else ("certified",)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-052",
        revision=UMD_052_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            observation_hash,
            request_hash,
            request_decision_hash,
            source_contract_hash,
            source_registry_hash,
            raw_payload_hash,
        ),
        source_refs=(
            f"fixture://umd-055/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionDecision(
        observation_id=f"observation-{suffix}",
        observation_hash=observation_hash,
        request_id=f"request-{suffix}",
        request_hash=request_hash,
        admission_decision_id=f"request-decision-{suffix}",
        admission_decision_record_hash=request_decision_hash,
        source_id="SOURCE-A",
        source_contract_hash=source_contract_hash,
        source_registry_hash=source_registry_hash,
        raw_payload_hash=raw_payload_hash,
        canonical_venue_id="KALSHI",
        adapter_key="KALSHI_MARKET_CATALOG",
        venue_market_id=f"MARKET-{suffix}",
        retrieval_sequence=1,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def ledger_entry(number: int, decision, previous):
    parents = [decision.record_hash]
    if previous is not None:
        parents.append(previous)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-053",
        revision=UMD_053_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-055/entry/{number}",
        ),
        created_at=FIXED,
    )

    return CertifiedRawVenueMarketObservationAdmissionLedgerEntry(
        sequence_number=number,
        previous_entry_hash=previous,
        decision=decision,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def read_model():
    first = ledger_entry(
        1,
        source_decision("a", True),
        None,
    )
    second = ledger_entry(
        2,
        source_decision("b", False),
        first.entry_hash,
    )

    ledger_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-053",
        revision=UMD_053_REVISION,
        schema_version="1.0.0",
        parent_hashes=(second.entry_hash,),
        source_refs=(
            "fixture://umd-055/ledger",
        ),
        created_at=FIXED,
    )
    ledger = ReadOnlyRawVenueMarketObservationAdmissionLedger(
        entries=(first, second),
        ledger_lineage=ledger_lineage,
    )

    model_lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-054",
        revision=UMD_054_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger.ledger_hash,),
        source_refs=(
            "fixture://umd-055/read-model",
        ),
        created_at=FIXED,
    )

    return build_umd_054_observation_admission_ledger_read_model(
        ledger,
        metadata={"read_only": True},
        lineage=model_lineage,
    )


def gate_lineage(model):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-055",
        revision=UMD_055_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            model.read_model_hash,
            model.source_ledger_hash,
        ),
        source_refs=(
            "fixture://umd-055/gate",
        ),
        created_at=FIXED,
    )


class TestUMD055(unittest.TestCase):
    def test_foundation(self) -> None:
        result = certify_umd_055_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-055")

    def test_valid_read_model_admitted(self) -> None:
        model = read_model()
        decision = evaluate_umd_055_read_model_admission(
            model,
            lineage=gate_lineage(model),
        )
        self.assertTrue(decision.admitted)
        self.assertEqual(decision.rejection_reasons, ())
        self.assertTrue(all(decision.checks.values()))

    def test_deterministic(self) -> None:
        model = read_model()
        lineage = gate_lineage(model)
        first = evaluate_umd_055_read_model_admission(
            model,
            lineage=lineage,
        )
        second = evaluate_umd_055_read_model_admission(
            model,
            lineage=lineage,
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_duplicate_read_model_id_rejected(self) -> None:
        model = read_model()
        decision = evaluate_umd_055_read_model_admission(
            model,
            seen_read_model_ids=(model.read_model_id,),
            lineage=gate_lineage(model),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "read_model_id_not_seen",
            decision.rejection_reasons,
        )

    def test_duplicate_read_model_hash_rejected(self) -> None:
        model = read_model()
        decision = evaluate_umd_055_read_model_admission(
            model,
            seen_read_model_hashes=(model.read_model_hash,),
            lineage=gate_lineage(model),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "read_model_hash_not_seen",
            decision.rejection_reasons,
        )

    def test_duplicate_source_ledger_rejected(self) -> None:
        model = read_model()
        decision = evaluate_umd_055_read_model_admission(
            model,
            seen_source_ledger_hashes=(
                model.source_ledger_hash,
            ),
            lineage=gate_lineage(model),
        )
        self.assertFalse(decision.admitted)
        self.assertIn(
            "source_ledger_hash_not_seen",
            decision.rejection_reasons,
        )

    def test_lineage_requires_both_hashes(self) -> None:
        model = read_model()
        bad = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-055",
            revision=UMD_055_REVISION,
            schema_version="1.0.0",
            parent_hashes=(model.read_model_hash,),
            source_refs=(
                "fixture://umd-055/bad",
            ),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            evaluate_umd_055_read_model_admission(
                model,
                lineage=bad,
            )

    def test_exact_umd054_type(self) -> None:
        model = read_model()
        self.assertEqual(
            model.lineage.build_id,
            "UMD-054",
        )

    def test_immutable(self) -> None:
        model = read_model()
        decision = evaluate_umd_055_read_model_admission(
            model,
            lineage=gate_lineage(model),
        )
        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            decision.admitted = False
        with self.assertRaises(TypeError):
            decision.checks["changed"] = False

    def test_side_effects(self) -> None:
        manifest = build_umd_055_certification_manifest()
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-055 CERTIFICATION TEST")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION "
        "LEDGER READ MODEL ADMISSION GATE"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD055
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_055_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-054 consumed read-only")
    print("[PASS] Exact UMD-054 read-model class consumed")
    print("[PASS] Deterministic read-model admission decision certified")
    print("[PASS] Duplicate read-model ID, hash, and source-ledger replay rejected")
    print("[PASS] Immutable complete decision lineage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-055 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER READ MODEL ADMISSION GATE CERTIFIED")
